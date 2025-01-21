from sqlalchemy.orm import Session
from alter.db_config import provide_session
from alter.models import LocationDistance
from alter.utils import (main_logger as logger,
                        error_logger,
                        db_logger)
from sqlalchemy import text
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from itertools import product
import multiprocessing

class DistanceCalculator:
    def __init__(self, max_distance=1000, grid_size=0.01):
        self.max_distance = max_distance
        self.grid_size = grid_size
        self.earth_radius = 6371000
        self.batch_size = 1000
        self.num_cores = multiprocessing.cpu_count()

    def _quick_distance_filter(self, prop_lat, prop_lon, addr_lat, addr_lon):
        """대략적인 거리 필터링"""
        lat_diff = abs(prop_lat - addr_lat) * 111000
        lon_diff = abs(prop_lon - addr_lon) * 88000
        return lat_diff <= self.max_distance and lon_diff <= self.max_distance

    def _save_batch(self, session, results):
        """배치 저장 처리"""
        try:
            batch = [
                LocationDistance(
                    property_id=prop_id,
                    address_id=addr_id,
                    distance=distance
                )
                for prop_id, addr_id, distance in results
            ]
            session.bulk_save_objects(batch)
            session.commit()
            logger.info(f"{len(batch)}개 거리 데이터 저장 완료")
        except Exception as e:
            logger.error(f"배치 저장 중 오류: {str(e)}")
            session.rollback()
            raise

    def process_location_chunk(self, args):
        chunk, address_grid = args
        results = []
        
        for prop_loc in chunk:
            prop_id, prop_lat, prop_lon = prop_loc
            grid_coords = self._get_grid_coordinates(prop_lon, prop_lat)
            
            for addr in self._get_nearby_addresses(grid_coords, address_grid):
                addr_id, addr_lat, addr_lon = addr
                
                if self._quick_distance_filter(prop_lat, prop_lon, addr_lat, addr_lon):
                    distance = self.calculate_distance(prop_lat, prop_lon, addr_lat, addr_lon)
                    if distance and distance <= self.max_distance:
                        results.append((prop_id, addr_id, distance))
        
        return results

    def _get_grid_coordinates(self, lon, lat):
        """그리드 좌표 계산"""
        return (int(lon / self.grid_size), int(lat / self.grid_size))

    def _get_nearby_addresses(self, grid_coords, address_grid):
        """주변 그리드의 주소들 반환"""
        grid_x, grid_y = grid_coords
        nearby_addresses = []
        for gx, gy in self.get_nearby_grids(grid_x, grid_y):
            if (gx, gy) in address_grid:
                nearby_addresses.extend(address_grid[(gx, gy)])
        return nearby_addresses

    @staticmethod
    def create_grid_index(locations, grid_size=0.01):
        """위치 데이터를 그리드로 인덱싱"""
        grid = {}
        for loc in locations:
            grid_x = int(float(loc[2]) / grid_size)
            grid_y = int(float(loc[1]) / grid_size)
            grid_key = (grid_x, grid_y)
            if grid_key not in grid:
                grid[grid_key] = []
            grid[grid_key].append(loc)
        return grid

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Haversine 공식을 사용한 두 지점 간의 거리 계산"""
        try:
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            
            a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
                math.cos(phi1) * math.cos(phi2) * \
                math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
            
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return self.earth_radius * c
        except Exception as e:
            logger.error(f"거리 계산 오류: {str(e)}")
            return None

    def get_nearby_grids(self, grid_x, grid_y):
        """주변 그리드 좌표 반환"""
        return list(product(
            range(grid_x - 1, grid_x + 2),
            range(grid_y - 1, grid_y + 2)
        ))

    def calculate_distances_for_chunk(self, chunk, address_grid):
        """청크 단위로 거리 계산"""
        results = []
        try:
            for prop_id, prop_lat, prop_lon in chunk:
                # 그리드 좌표 계산
                grid_x = int(float(prop_lon) / self.grid_size)
                grid_y = int(float(prop_lat) / self.grid_size)
                
                # 주변 그리드 검색
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (0,0)]:
                    grid_key = (grid_x + dx, grid_y + dy)
                    if grid_key in address_grid:
                        for addr_id, addr_lat, addr_lon in address_grid[grid_key]:
                            # 빠른 거리 필터링
                            if self._quick_distance_filter(prop_lat, prop_lon, addr_lat, addr_lon):
                                distance = self.calculate_distance(prop_lat, prop_lon, addr_lat, addr_lon)
                                if distance and distance <= self.max_distance:
                                    results.append((prop_id, addr_id, distance))
            
            return results
        except Exception as e:
            logger.error(f"청크 처리 중 오류 발생: {str(e)}")
            raise

@provide_session
def calculate_distances(session=None, batch_size=1000):
    calculator = DistanceCalculator()
    
    try:
        logger.info("거리 계산 시작...")
        
        # 중복 체크를 위한 세트 초기화
        processed_pairs = set()
        
        # 기존 거리 데이터 로드
        logger.info("기존 거리 데이터 로드 중...")
        existing_pairs = session.execute(text("""
            SELECT property_id, address_id 
            FROM realestate.location_distances
        """)).fetchall()
        processed_pairs.update((p[0], p[1]) for p in existing_pairs)
        logger.info(f"기존 거리 데이터 {len(processed_pairs)}쌍 로드 완료")
        
        # SQL 쿼리 수정 - 중복 체크 추가
        logger.info("새로운 매물-주소 조합 조회 중...")
        new_pairs = session.execute(text("""
            WITH property_batch AS (
                SELECT DISTINCT p.property_id, p.latitude, p.longitude
                FROM realestate.property_locations p
                WHERE p.latitude IS NOT NULL 
                AND p.longitude IS NOT NULL
                AND p.latitude != 'NaN'
                AND p.longitude != 'NaN'
                AND p.latitude BETWEEN -90 AND 90
                AND p.longitude BETWEEN -180 AND 180
                LIMIT :batch_size
            ),
            valid_addresses AS (
                SELECT a.id, a.latitude, a.longitude
                FROM realestate.addresses a
                WHERE a.latitude IS NOT NULL 
                AND a.longitude IS NOT NULL
                AND a.latitude != 'NaN'
                AND a.longitude != 'NaN'
                AND a.latitude BETWEEN -90 AND 90
                AND a.longitude BETWEEN -180 AND 180
            ),
            existing_distances AS (
                SELECT DISTINCT property_id, address_id
                FROM realestate.location_distances
            )
            SELECT DISTINCT 
                p.property_id, p.latitude, p.longitude,
                a.id as address_id, a.latitude, a.longitude
            FROM property_batch p
            CROSS JOIN valid_addresses a
            WHERE NOT EXISTS (
                SELECT 1 
                FROM existing_distances d
                WHERE d.property_id = p.property_id 
                AND d.address_id = a.id
            )
        """), {'batch_size': 100}).fetchall()
        
        logger.info(f"새로운 거리 계산 필요: {len(new_pairs)}쌍")
        
        # 추가 데이터 검증
        valid_pairs = [
            pair for pair in new_pairs 
            if all(isinstance(x, (int, float)) and not math.isnan(float(x)) 
                  for x in (pair[1], pair[2], pair[4], pair[5]))
        ]
        
        logger.info(f"유효한 좌표를 가진 쌍: {len(valid_pairs)}/{len(new_pairs)}")
        
        if not valid_pairs:
            logger.info("계산할 유효한 거리 데이터가 없습니다.")
            return True
        
        # 주소 데이터 그리드 인덱싱
        logger.info("주소 데이터 그리드 인덱싱 시작...")
        address_data = [(p[3], p[4], p[5]) for p in valid_pairs]
        address_grid = calculator.create_grid_index(list(set(address_data)))
        logger.info(f"총 {len(set(address_data))}개의 고유 주소 인덱싱 완료")
        
        # 매물 데이터 준비 (더 작은 배치로 나누기)
        property_data = [(p[0], p[1], p[2]) for p in valid_pairs]
        property_data = list(set(property_data))
        logger.info(f"총 {len(property_data)}개의 고유 매물 데이터 준비 완료")
        
        # 더 작은 청크로 나누어 순차 처리
        chunk_size = 10  # 작은 청크 사이즈
        results = []
        total_chunks = len(property_data) // chunk_size + (1 if len(property_data) % chunk_size else 0)
        
        for i in range(0, len(property_data), chunk_size):
            chunk = property_data[i:i + chunk_size]
            logger.info(f"청크 처리 중: {i//chunk_size + 1}/{total_chunks}")
            
            try:
                chunk_results = calculator.calculate_distances_for_chunk(chunk, address_grid)
                results.extend(chunk_results)
                
                # 중간 저장
                if len(results) >= batch_size:
                    try:
                        # 중복 제거
                        unique_results = []
                        for r in results[:batch_size]:
                            pair = (r[0], r[1])  # property_id, address_id
                            if pair not in processed_pairs:
                                unique_results.append(r)
                                processed_pairs.add(pair)
                        
                        if unique_results:
                            session.bulk_insert_mappings(
                                LocationDistance,
                                [
                                    {
                                        'property_id': r[0],
                                        'address_id': r[1],
                                        'distance': r[2]
                                    }
                                    for r in unique_results
                                ]
                            )
                            session.commit()
                            logger.info(f"중간 저장 완료: {len(unique_results)}개")
                        results = results[batch_size:]
                    except Exception as e:
                        logger.error(f"중간 저장 중 오류 발생: {str(e)}")
                        session.rollback()
                
            except Exception as e:
                logger.error(f"청크 {i//chunk_size + 1} 처리 중 오류 발생: {str(e)}")
                continue
        
        # 남은 결과 저장
        if results:
            try:
                unique_results = []
                for r in results:
                    pair = (r[0], r[1])
                    if pair not in processed_pairs:
                        unique_results.append(r)
                        processed_pairs.add(pair)
                
                if unique_results:
                    session.bulk_insert_mappings(
                        LocationDistance,
                        [
                            {
                                'property_id': r[0],
                                'address_id': r[1],
                                'distance': r[2]
                            }
                            for r in unique_results
                        ]
                    )
                    session.commit()
                    logger.info(f"최종 저장 완료: {len(unique_results)}개")
            except Exception as e:
                logger.error(f"최종 저장 중 오류 발생: {str(e)}")
                session.rollback()
        
        logger.info("모든 거리 계산 및 저장 완료")
        return True
        
    except Exception as e:
        logger.error(f"거리 계산 중 오류 발생: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    calculate_distances() 