from sqlalchemy.orm import Session
from alter.db_config import provide_session
from alter.models import LocationDistance
from alter.utils import (main_logger as logger,
                        error_logger,
                        db_logger)
from sqlalchemy import text
import math
from concurrent.futures import ProcessPoolExecutor
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

@provide_session
def calculate_distances(session=None, batch_size=1000):
    """거리 계산 메인 함수"""
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
        with ProcessPoolExecutor(max_workers=num_cores) as executor:
            futures = [
                executor.submit(calculator.process_location_chunk, 
                             (chunk, address_grid))
                for chunk in chunks
            ]
            
            # 진행률 표시와 함께 결과 수집
            for future in tqdm(futures, desc="청크 처리"):
                chunk_results = future.result()
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
        raise

if __name__ == "__main__":
    calculate_distances() 