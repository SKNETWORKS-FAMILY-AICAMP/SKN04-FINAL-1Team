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

@provide_session
def calculate_distances(session=None, batch_size=1000):
    calculator = DistanceCalculator()
    
    try:
        logger.info("거리 계산 시작...")
        
        # 주소 데이터 로드 및 검증
        addresses = session.execute(text("""
            SELECT id, latitude, longitude 
            FROM realestate.addresses 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND latitude BETWEEN -90 AND 90 
            AND longitude BETWEEN -180 AND 180
        """)).fetchall()
        
        logger.info(f"로드된 주소 데이터: {len(addresses)}개")
        
        # 주소 그리드 생성
        address_grid = calculator.create_grid_index(addresses)
        logger.info(f"생성된 그리드 수: {len(address_grid)}")
        
        # 스키마 생성 확인
        session.execute(text("CREATE SCHEMA IF NOT EXISTS realestate;"))
        session.execute(text("""
            DROP TABLE IF EXISTS realestate.location_distances CASCADE;
            CREATE TABLE realestate.location_distances (
                id SERIAL PRIMARY KEY,
                property_id BIGINT NOT NULL,
                address_id INTEGER NOT NULL,
                distance DOUBLE PRECISION NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_property_address UNIQUE (property_id, address_id),
                CONSTRAINT fk_property FOREIGN KEY (property_id) REFERENCES realestate.property_locations(property_id),
                CONSTRAINT fk_address FOREIGN KEY (address_id) REFERENCES realestate.addresses(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_location_distances_property ON realestate.location_distances(property_id);
            CREATE INDEX IF NOT EXISTS idx_location_distances_address ON realestate.location_distances(address_id);
        """))
        session.commit()
        
        # 데이터베이스 상태 확인
        property_count = session.execute(text("SELECT COUNT(*) FROM realestate.property_locations")).scalar()
        address_count = session.execute(text("SELECT COUNT(*) FROM realestate.addresses")).scalar()
        logger.info(f"데이터베이스 상태: property_locations={property_count}개, addresses={address_count}개")
        
        # 유효한 좌표를 가진 데이터 수 확인
        valid_properties = session.execute(text("""
            SELECT COUNT(*) 
            FROM realestate.property_locations 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND CAST(latitude AS TEXT) != 'NaN'
            AND CAST(longitude AS TEXT) != 'NaN'
            AND CAST(latitude AS DOUBLE PRECISION) BETWEEN -90 AND 90
            AND CAST(longitude AS DOUBLE PRECISION) BETWEEN -180 AND 180
        """)).scalar()
        
        valid_addresses = session.execute(text("""
            SELECT COUNT(*) 
            FROM realestate.addresses 
            WHERE latitude IS NOT NULL 
            AND longitude IS NOT NULL 
            AND CAST(latitude AS TEXT) != 'NaN'
            AND CAST(longitude AS TEXT) != 'NaN'
            AND latitude BETWEEN -90 AND 90
            AND longitude BETWEEN -180 AND 180
        """)).scalar()
        
        logger.info(f"유효한 좌표를 가진 데이터: property_locations={valid_properties}개, addresses={valid_addresses}개")
        
        # 기존 거리 데이터 로드
        logger.info("기존 거리 데이터 로드 중...")
        existing_pairs = session.execute(text("""
            SELECT property_id, address_id 
            FROM realestate.location_distances
        """)).fetchall()
        calculator.processed_pairs.update((p[0], p[1]) for p in existing_pairs)
        logger.info(f"기존 거리 데이터 {len(calculator.processed_pairs)}쌍 로드 완료")
        
        # SQL 쿼리 최적화 - 인덱스 힌트 추가
        logger.info("새로운 매물-주소 조합 조회 중...")
        new_pairs = session.execute(text("""
            WITH property_batch AS (
                SELECT DISTINCT 
                    p.property_id, 
                    CAST(p.latitude AS DOUBLE PRECISION) as latitude,
                    CAST(p.longitude AS DOUBLE PRECISION) as longitude
                FROM realestate.property_locations p
                WHERE p.latitude IS NOT NULL 
                AND p.longitude IS NOT NULL 
                AND CAST(p.latitude AS TEXT) != 'NaN'
                AND CAST(p.longitude AS TEXT) != 'NaN'
                AND CAST(p.latitude AS DOUBLE PRECISION) BETWEEN -90 AND 90
                AND CAST(p.longitude AS DOUBLE PRECISION) BETWEEN -180 AND 180
                LIMIT :batch_size
            ),
            valid_addresses AS (
                SELECT 
                    a.id, 
                    a.latitude,
                    a.longitude
                FROM realestate.addresses a
                WHERE a.latitude IS NOT NULL 
                AND a.longitude IS NOT NULL 
                AND CAST(a.latitude AS TEXT) != 'NaN'
                AND CAST(a.longitude AS TEXT) != 'NaN'
                AND a.latitude BETWEEN -90 AND 90
                AND a.longitude BETWEEN -180 AND 180
            )
            SELECT DISTINCT 
                p.property_id, p.latitude, p.longitude,
                a.id as address_id, a.latitude, a.longitude
            FROM property_batch p
            CROSS JOIN valid_addresses a
            WHERE NOT EXISTS (
                SELECT 1 
                FROM realestate.location_distances d
                WHERE d.property_id = p.property_id 
                AND d.address_id = a.id
            )
            AND ABS(p.latitude - a.latitude) * 111000 <= :max_distance
            AND ABS(p.longitude - a.longitude) * 111000 * 
                COS(RADIANS((p.latitude + a.latitude) / 2)) <= :max_distance
        """), {
            'batch_size': batch_size,
            'max_distance': calculator.max_distance
        }).fetchall()
        
        logger.info(f"새로운 거리 계산 필요: {len(new_pairs)}쌍")
        
        # 추가 데이터 검증
        valid_pairs = []
        for pair in new_pairs:
            try:
                prop_lat = float(pair[1])
                prop_lon = float(pair[2])
                addr_lat = float(pair[4])
                addr_lon = float(pair[5])
                
                if (not math.isnan(prop_lat) and not math.isnan(prop_lon) and
                    not math.isnan(addr_lat) and not math.isnan(addr_lon) and
                    -90 <= prop_lat <= 90 and -180 <= prop_lon <= 180 and
                    -90 <= addr_lat <= 90 and -180 <= addr_lon <= 180):
                    valid_pair = (
                        pair[0],
                        prop_lat,
                        prop_lon,
                        pair[3],
                        addr_lat,
                        addr_lon
                    )
                    valid_pairs.append(valid_pair)
            except (ValueError, TypeError) as e:
                logger.debug(f"좌표 변환 실패: {pair} - {str(e)}")
                continue
        
        logger.info(f"유효한 좌표를 가진 쌍: {len(valid_pairs)}/{len(new_pairs)}")
        
        if not valid_pairs:
            logger.info("계산할 유효한 거리 데이터가 없습니다.")
            return True
        
        # 매물 데이터 준비
        property_data = [(p[0], p[1], p[2]) for p in valid_pairs]
        property_data = list(set(property_data))
        logger.info(f"총 {len(property_data)}개의 고유 매물 데이터 준비 완료")
        
        # 청크 크기 조정
        chunk_size = 50  # 더 작은 청크 크기 사용
        results = []
        total_chunks = len(property_data) // chunk_size + (1 if len(property_data) % chunk_size else 0)
        
        for i in range(0, len(property_data), chunk_size):
            chunk = property_data[i:i + chunk_size]
            logger.info(f"청크 처리 중: {i//chunk_size + 1}/{total_chunks}")
            
            try:
                chunk_results = calculator.calculate_distances_for_chunk(chunk, address_grid)
                results.extend(chunk_results)
                
                # 더 작은 크기로 자주 저장
                if len(results) >= 500:
                    logger.info(f"중간 저장 시작: {len(results)}개의 결과")
                    calculator.save_results(session, results)
                    results = []
                
            except Exception as e:
                logger.error(f"청크 {i//chunk_size + 1} 처리 중 오류 발생: {str(e)}")
                continue
        
        # 남은 결과 저장
        if results:
            logger.info(f"최종 저장 시작: {len(results)}개의 결과")
            calculator.save_results(session, results)
        
        logger.info("모든 거리 계산 및 저장 완료")
        return True
        
    except Exception as e:
        logger.error(f"거리 계산 중 오류 발생: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    calculate_distances() 