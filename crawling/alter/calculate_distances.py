from sqlalchemy.orm import Session
from db_config import engine
from models import LocationDistance
from sqlalchemy import text
import math
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
from itertools import product
import multiprocessing

def create_grid_index(locations, grid_size=0.01):
    """위치 데이터를 그리드로 인덱싱"""
    grid = {}
    for loc in locations:
        # 그리드 좌표 계산 (약 1km 간격)
        grid_x = int(float(loc[2]) / grid_size)
        grid_y = int(float(loc[1]) / grid_size)
        
        # 그리드에 위치 추가
        grid_key = (grid_x, grid_y)
        if grid_key not in grid:
            grid[grid_key] = []
        grid[grid_key].append(loc)
    return grid

def get_nearby_grids(grid_x, grid_y):
    """주변 그리드 좌표 반환"""
    return list(product(
        range(grid_x - 1, grid_x + 2),
        range(grid_y - 1, grid_y + 2)
    ))

def process_location_chunk(args):
    """각 프로세스에서 처리할 매물 청크"""
    chunk, address_grid, max_distance = args
    results = []
    
    for prop_loc in chunk:
        prop_id = prop_loc[0]
        prop_lat = float(prop_loc[1])
        prop_lon = float(prop_loc[2])
        
        # 현재 위치의 그리드 좌표
        grid_x = int(prop_lon / 0.01)
        grid_y = int(prop_lat / 0.01)
        
        # 주변 그리드에서 주소 검색
        nearby_addresses = []
        for gx, gy in get_nearby_grids(grid_x, grid_y):
            if (gx, gy) in address_grid:
                nearby_addresses.extend(address_grid[(gx, gy)])
        
        # 거리 계산 및 필터링
        for addr in nearby_addresses:
            addr_id = addr[0]
            addr_lat = float(addr[1])
            addr_lon = float(addr[2])
            
            # 대략적인 거리로 먼저 필터링
            lat_diff = abs(prop_lat - addr_lat) * 111000
            lon_diff = abs(prop_lon - addr_lon) * 88000
            
            if lat_diff <= max_distance and lon_diff <= max_distance:
                # 정확한 거리 계산
                distance = calculate_distance(prop_lat, prop_lon, addr_lat, addr_lon)
                if distance <= max_distance:
                    results.append((prop_id, addr_id, distance))
    
    return results

def calculate_distances():
    """1km 이내의 매물과 주요 시설 간의 거리만 계산 (멀티프로세싱 버전)"""
    MAX_DISTANCE = 1000  # 1km in meters
    
    with Session(engine) as session:
        try:
            # 데이터 로드
            property_locations = session.execute(text("""
                SELECT property_id, latitude, longitude 
                FROM property_locations 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)).fetchall()
            
            addresses = session.execute(text("""
                SELECT address_id, latitude, longitude 
                FROM addresses 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)).fetchall()
            
            print(f"매물 수: {len(property_locations)}")
            print(f"주요 시설 수: {len(addresses)}")
            
            # 주소 데이터 그리드 인덱싱
            address_grid = create_grid_index(addresses)
            
            # CPU 코어 수에 따라 데이터 분할
            num_cores = multiprocessing.cpu_count()
            chunk_size = len(property_locations) // num_cores
            chunks = [
                property_locations[i:i + chunk_size]
                for i in range(0, len(property_locations), chunk_size)
            ]
            
            # 멀티프로세싱으로 거리 계산
            results = []
            with ProcessPoolExecutor(max_workers=num_cores) as executor:
                futures = [
                    executor.submit(process_location_chunk, 
                                 (chunk, address_grid, MAX_DISTANCE))
                    for chunk in chunks
                ]
                
                # 진행률 표시와 함께 결과 수집
                for future in tqdm(futures, desc="청크 처리"):
                    results.extend(future.result())
            
            # 결과를 배치로 저장
            print("데이터베이스에 저장 중...")
            batch_size = 1000
            for i in tqdm(range(0, len(results), batch_size), desc="저장 진행률"):
                batch = [
                    LocationDistance(
                        property_id=prop_id,
                        address_id=addr_id,
                        distance=distance
                    )
                    for prop_id, addr_id, distance in results[i:i + batch_size]
                ]
                session.bulk_save_objects(batch)
                session.commit()
            
            print("거리 계산 완료!")
            print(f"총 {len(results)}개의 거리 데이터 저장됨")
            
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            session.rollback()
            raise e

def calculate_distance(lat1, lon1, lat2, lon2):
    """Haversine 공식을 사용한 두 지점 간의 거리 계산 (미터)"""
    R = 6371000  # 지구 반경 (미터)
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

if __name__ == "__main__":
    calculate_distances() 