from sqlalchemy.orm import Session
from alter.db_config import provide_session
from alter.models import LocationDistance, PropertyLocation
from alter.utils import (main_logger as logger,
                        error_logger,
                        db_logger)
from sqlalchemy import text
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from itertools import product
import multiprocessing
import logging

# 로깅 레벨 설정
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class DistanceCalculator:
    def __init__(self, max_distance=1000, grid_size=0.01):
        self.max_distance = max_distance
        self.grid_size = grid_size
        self.earth_radius = 6371000
        self.batch_size = 1000
        self.num_cores = multiprocessing.cpu_count()
        self.processed_pairs = set()

    def _quick_distance_filter(self, prop_lat, prop_lon, addr_lat, addr_lon):
        """대략적인 거리 필터링 - 여유 있게 설정"""
        try:
            lat_diff = abs(prop_lat - addr_lat) * 111000
            lon_diff = abs(prop_lon - addr_lon) * 111000 * math.cos(math.radians((prop_lat + addr_lat) / 2))
            
            # 필터링 거리를 실제 최대 거리보다 20% 더 크게 설정
            filter_distance = self.max_distance * 1.2
            
            result = lat_diff <= filter_distance and lon_diff <= filter_distance
            if not result:
                logger.debug(f"거리 필터링: lat_diff={lat_diff}m, lon_diff={lon_diff}m, filter_distance={filter_distance}m")
            
            return result
        except Exception as e:
            logger.error(f"거리 필터링 중 오류 발생: {str(e)}")
            return False

    def save_results(self, session, results_to_save):
        """결과를 데이터베이스에 저장"""
        if not results_to_save:
            return
        
        try:
            # 결과 데이터 검증
            valid_results = []
            for r in results_to_save:
                try:
                    property_id = int(r[0])
                    address_id = int(r[1])
                    distance = float(r[2])
                    
                    if math.isnan(distance) or distance <= 0 or distance > self.max_distance:
                        logger.warning(f"유효하지 않은 거리: property_id={property_id}, "
                                     f"address_id={address_id}, distance={distance}")
                        continue
                    
                    pair = (property_id, address_id)
                    if pair not in self.processed_pairs:
                        valid_results.append((property_id, address_id, distance))
                        self.processed_pairs.add(pair)
                except (ValueError, TypeError) as e:
                    logger.error(f"데이터 변환 실패: {r} - {str(e)}")
                    continue
            
            if not valid_results:
                logger.info("저장할 유효한 결과가 없습니다.")
                return
            
            logger.info(f"저장 시도: {len(valid_results)}개의 유효한 결과")
            
            # 배치 단위로 저장
            batch_size = 100
            total_saved = 0
            
            for i in range(0, len(valid_results), batch_size):
                batch = valid_results[i:i + batch_size]
                try:
                    # 데이터 존재 여부 확인
                    property_ids = [r[0] for r in batch]
                    address_ids = [r[1] for r in batch]
                    
                    existing_properties = session.execute(text("""
                        SELECT property_id 
                        FROM realestate.property_locations 
                        WHERE property_id = ANY(:ids)
                    """), {'ids': property_ids}).fetchall()
                    
                    existing_addresses = session.execute(text("""
                        SELECT id 
                        FROM realestate.addresses 
                        WHERE id = ANY(:ids)
                    """), {'ids': address_ids}).fetchall()
                    
                    valid_properties = {p[0] for p in existing_properties}
                    valid_addresses = {a[0] for a in existing_addresses}
                    
                    # 유효한 데이터만 필터링
                    filtered_batch = [
                        r for r in batch 
                        if r[0] in valid_properties and r[1] in valid_addresses
                    ]
                    
                    if not filtered_batch:
                        logger.warning(f"배치에 유효한 데이터가 없습니다: "
                                     f"properties={len(valid_properties)}/{len(property_ids)}, "
                                     f"addresses={len(valid_addresses)}/{len(address_ids)}")
                        continue
                    
                    # SQL 생성
                    values = []
                    for r in filtered_batch:
                        values.append(f"({r[0]}::bigint, {r[1]}::integer, {r[2]}::double precision)")
                    
                    insert_sql = f"""
                        INSERT INTO realestate.location_distances 
                        (property_id, address_id, distance)
                        VALUES {', '.join(values)}
                        ON CONFLICT (property_id, address_id) DO NOTHING
                        RETURNING id;
                    """
                    
                    # 실행 및 커밋
                    result = session.execute(text(insert_sql))
                    inserted_ids = result.fetchall()
                    session.commit()
                    
                    total_saved += len(inserted_ids)
                    logger.info(f"배치 저장 완료: {len(inserted_ids)}개 저장됨 "
                              f"(배치 크기: {len(filtered_batch)}, "
                              f"누적: {total_saved}개)")
                    
                except Exception as e:
                    logger.error(f"배치 저장 중 오류 발생: {str(e)}")
                    session.rollback()
                    continue
            
            # 최종 결과 확인
            total_count = session.execute(text(
                "SELECT COUNT(*) FROM realestate.location_distances"
            )).scalar()
            
            logger.info(f"저장 완료: 총 {total_saved}개 저장됨")
            logger.info(f"테이블 전체 데이터: {total_count}개")
            logger.info(f"현재까지 총 처리된 쌍: {len(self.processed_pairs)}개")
            
        except Exception as e:
            logger.error(f"저장 중 오류 발생: {str(e)}")
            session.rollback()

    def calculate_distances_for_chunk(self, chunk, address_grid):
        """청크 단위로 거리 계산"""
        results = []
        try:
            logger.info(f"청크 크기: {len(chunk)}")
            for prop_id, prop_lat, prop_lon in chunk:
                try:
                    # 좌표 타입 변환
                    prop_lat = float(prop_lat)
                    prop_lon = float(prop_lon)
                    
                    # 그리드 좌표 계산
                    grid_x = int(prop_lon / self.grid_size)
                    grid_y = int(prop_lat / self.grid_size)
                    
                    logger.info(f"매물 {prop_id} 처리 중: 좌표=({prop_lat}, {prop_lon}), 그리드=({grid_x}, {grid_y})")
                    
                    # 주변 그리드 검색
                    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (0,0)]:
                        grid_key = (grid_x + dx, grid_y + dy)
                        if grid_key in address_grid:
                            addresses = address_grid[grid_key]
                            logger.info(f"매물 {prop_id}의 그리드 {grid_key}에서 {len(addresses)}개의 주소 발견")
                            
                            for addr_id, addr_lat, addr_lon in addresses:
                                try:
                                    # 좌표 타입 변환
                                    addr_lat = float(addr_lat)
                                    addr_lon = float(addr_lon)
                                    
                                    # 빠른 거리 필터링
                                    if self._quick_distance_filter(prop_lat, prop_lon, addr_lat, addr_lon):
                                        distance = self.calculate_distance(prop_lat, prop_lon, addr_lat, addr_lon)
                                        if distance and distance <= self.max_distance:
                                            logger.info(f"거리 계산 결과: 매물 {prop_id} ({prop_lat}, {prop_lon}) - "
                                                      f"주소 {addr_id} ({addr_lat}, {addr_lon}) = {distance}m")
                                            results.append((prop_id, addr_id, distance))
                                except (ValueError, TypeError) as e:
                                    logger.error(f"주소 좌표 처리 오류: {str(e)}, 데이터: {addr_id}, {addr_lat}, {addr_lon}")
                                    continue
                except (ValueError, TypeError) as e:
                    logger.error(f"매물 좌표 처리 오류: {str(e)}, 데이터: {prop_id}, {prop_lat}, {prop_lon}")
                    continue
            
            logger.info(f"청크에서 계산된 총 거리: {len(results)}개")
            return results
        except Exception as e:
            logger.error(f"청크 처리 중 오류 발생: {str(e)}")
            raise

    @staticmethod
    def create_grid_index(locations, grid_size=0.01):
        """위치 데이터를 그리드로 인덱싱"""
        try:
            grid = {}
            total_locations = len(locations)
            logger.info(f"그리드 인덱싱 시작: 총 {total_locations}개의 위치")
            
            for i, loc in enumerate(locations, 1):
                try:
                    grid_x = int(float(loc[2]) / grid_size)
                    grid_y = int(float(loc[1]) / grid_size)
                    grid_key = (grid_x, grid_y)
                    
                    if grid_key not in grid:
                        grid[grid_key] = []
                    grid[grid_key].append(loc)
                    
                    if i % 1000 == 0:
                        logger.info(f"그리드 인덱싱 진행: {i}/{total_locations} ({i/total_locations*100:.1f}%)")
                except (ValueError, TypeError, IndexError) as e:
                    logger.error(f"위치 데이터 처리 오류: {str(e)}, 데이터: {loc}")
                    continue
            
            total_grids = len(grid)
            total_indexed = sum(len(points) for points in grid.values())
            logger.info(f"그리드 인덱싱 완료: {total_grids}개의 그리드, {total_indexed}개의 위치 인덱싱됨")
            
            return grid
        except Exception as e:
            logger.error(f"그리드 인덱싱 중 오류 발생: {str(e)}")
            raise

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
            
            distance = self.earth_radius * c
            logger.debug(f"거리 계산: ({lat1}, {lon1}) -> ({lat2}, {lon2}) = {distance}m")
            
            return distance
        except Exception as e:
            logger.error(f"거리 계산 오류: {str(e)}, 좌표: ({lat1}, {lon1}) -> ({lat2}, {lon2})")
            return None

    def get_nearby_grids(self, grid_x, grid_y):
        """주변 그리드 좌표 반환"""
        return list(product(
            range(grid_x - 1, grid_x + 2),
            range(grid_y - 1, grid_y + 2)
        ))

@provide_session
def calculate_distances(session=None, batch_size=1000):
    calculator = DistanceCalculator()
    
    try:
        # 새로운 매물과 주소 데이터 로드
        new_pairs = session.execute(text("""
            WITH new_combinations AS (
                SELECT DISTINCT p.property_id, p.latitude, p.longitude, 
                       a.address_id, a.latitude, a.longitude
                FROM property_locations p
                CROSS JOIN addresses a
                LEFT JOIN location_distances d 
                    ON d.property_id = p.property_id 
                    AND d.address_id = a.address_id
                WHERE d.distance IS NULL
                    AND p.latitude IS NOT NULL 
                    AND p.longitude IS NOT NULL
                    AND a.latitude IS NOT NULL 
                    AND a.longitude IS NOT NULL
            )
            SELECT * FROM new_combinations
        """)).fetchall()
        
        print(f"새로운 거리 계산 필요: {len(new_pairs)}쌍")
        
        if not new_pairs:
            print("계산할 새로운 거리 데이터가 없습니다.")
            return True
        
        # 주소 데이터를 그리드로 인덱싱
        address_data = [(p[3], p[4], p[5]) for p in new_pairs]  # address_id, lat, lon
        address_grid = calculator.create_grid_index(list(set(address_data)))
        
        # 매물 데이터 준비
        property_data = [(p[0], p[1], p[2]) for p in new_pairs]  # property_id, lat, lon
        property_data = list(set(property_data))  # 중복 제거
        
        # CPU 코어 수에 따라 데이터 분할
        num_cores = multiprocessing.cpu_count()
        chunk_size = max(1, len(property_data) // num_cores)
        chunks = [
            property_data[i:i + chunk_size]
            for i in range(0, len(property_data), chunk_size)
        ]
        
        print(f"총 {len(chunks)}개 청크로 분할하여 처리 시작...")
        
        # 멀티프로세싱으로 거리 계산
        results = []
        total_chunks = len(property_data) // chunk_size + (1 if len(property_data) % chunk_size else 0)
        
        for i in range(0, len(property_data), chunk_size):
            chunk = property_data[i:i + chunk_size]
            logger.info(f"청크 처리 중: {i//chunk_size + 1}/{total_chunks}")
            
            try:
                chunk_results = calculator.calculate_distances_for_chunk(chunk, address_grid)
                results.extend(chunk_results)
                
                # 중간 결과 저장
                if len(results) >= batch_size:
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
                    results = []
            
            # 남은 결과 저장
            if results:
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
            
            print("거리 계산 완료!")
            return True
        
    except Exception as e:
        logger.error(f"거리 계산 중 오류 발생: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    calculate_distances() 