from sqlalchemy.orm import Session
from alter.db_config import provide_session
from alter.models import Address
from alter.utils import (retry_on_failure, get_api_key, 
                        main_logger as logger)
import requests
import time
from tqdm import tqdm
import json
import os
from airflow.models import Variable
from alter.exceptions import APIError
from alter.utils import timing_context, BatchProcessor
from airflow.models import Variable
from sqlalchemy.sql import text


KAKAO_API_KEY = Variable.get("KAKAO_API_KEY")

@retry_on_failure(max_attempts=3)
def get_coordinates_from_kakao(address):
    """카카오맵 API로 주소의 좌표 가져오기"""
    try:
        logger.info(f"카카오맵 API 호출 시작: {address}")
        url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
        params = {"query": address, "analyze_type": "exact"}
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"API 응답: {json.dumps(result, ensure_ascii=False)}")
        
        if not result.get('documents'):
            logger.warning(f"주소에 대한 결과 없음: {address}")
            return None
            
        location = result['documents'][0]
        coords = {
            'latitude': float(location['y']),
            'longitude': float(location['x'])
        }
        logger.info(f"좌표 찾음: {coords}")
        return coords
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API 요청 실패: {str(e)}")
        raise
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"API 응답 파싱 실패: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"알 수 없는 오류: {str(e)}")
        return None

@provide_session
def update_address_coordinates(session=None, batch_size=100):
    """좌표가 없는 주소들의 좌표 업데이트"""
    try:
        addresses = session.execute(text("""
            SELECT * FROM realestate.addresses 
            WHERE latitude IS NULL 
            OR longitude IS NULL 
            OR CAST(latitude AS TEXT) IN ('nan', 'NaN', 'NULL', '')
            OR CAST(longitude AS TEXT) IN ('nan', 'NaN', 'NULL', '')
        """)).fetchall()
        
        logger.info(f"좌표가 없는 주소 수: {len(addresses)}")
        
        stats = {'success': 0, 'error': 0}
        
        for address in tqdm(addresses, desc="좌표 업데이트"):
            try:
                logger.info(f"\n처리 중인 주소: {address.area_name}")
                coords = get_coordinates_from_kakao(address.area_name)
                
                if coords:
                    try:
                        session.execute(
                            text("""
                                UPDATE realestate.addresses 
                                SET latitude = :lat, 
                                    longitude = :lon,
                                    updated_at = NOW()
                                WHERE id = :addr_id
                            """),
                            {
                                'lat': coords['latitude'],
                                'lon': coords['longitude'],
                                'addr_id': address.id
                            }
                        )
                        session.commit()
                        stats['success'] += 1
                        logger.info(f"✓ 좌표 업데이트 성공: {coords}")
                    except Exception as e:
                        logger.error(f"DB 업데이트 실패: {str(e)}")
                        session.rollback()
                        stats['error'] += 1
                else:
                    logger.warning(f"좌표를 찾을 수 없음: {address.area_name}")
                    stats['error'] += 1
                
                time.sleep(0.1)  # API 호출 제한 준수
                
            except Exception as e:
                stats['error'] += 1
                logger.error(f"주소 처리 중 오류 ({address.area_name}): {str(e)}")
                continue
        
        logger.info(f"좌표 업데이트 완료! 성공: {stats['success']}, 실패: {stats['error']}")
        return True
        
    except Exception as e:
        logger.error(f"전체 프로세스 오류: {str(e)}")
        session.rollback()
        raise

def save_failed_addresses(failed_list):
    """실패한 주소들 저장"""
    with open('failed_addresses.json', 'w', encoding='utf-8') as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)

class AddressCoordinateUpdater:
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.stats = {'success': 0, 'error': 0}

    def _get_addresses_without_coordinates(self, session):
        """좌표가 없는 주소들 조회"""
        return session.query(Address).filter(
            (Address.latitude.is_(None)) | 
            (Address.longitude.is_(None)) |
            (Address.latitude == '') |
            (Address.longitude == '') |
            (Address.latitude == 'nan') |
            (Address.longitude == 'nan') |
            (Address.latitude == 'NaN') |
            (Address.longitude == 'NaN') |
            (Address.latitude == 'NULL') |
            (Address.longitude == 'NULL')
        ).all()

    @retry_on_failure(max_attempts=3)
    def _update_single_address(self, address, session):
        coords = get_coordinates_from_kakao(address.area_name)
        if coords:
            address.latitude = coords['latitude']
            address.longitude = coords['longitude']
            session.add(address)
            self.stats['success'] += 1
            return True
        self.stats['error'] += 1
        return False

    def update_coordinates(self, session):
        with timing_context("주소 좌표 업데이트"):
            addresses = self._get_addresses_without_coordinates(session)
            
            with BatchProcessor(self.batch_size) as batch:
                for address in tqdm(addresses):
                    if self._update_single_address(address, session):
                        batch.add(address)
                    time.sleep(0.1)  # API 제한 준수

            logger.info(f"업데이트 완료! 성공: {self.stats['success']}, 실패: {self.stats['error']}")

@provide_session
def update_missing_address_coordinates(session=None):
    """주소 좌표 업데이트"""
    try:
        updater = AddressCoordinateUpdater()
        updater.update_coordinates(session)
        return True
    except Exception as e:
        logger.error(f"주소 좌표 업데이트 중 오류 발생: {str(e)}")
        return False

@retry_on_failure(max_attempts=3)
def get_coordinates_from_kakao_for_property(sido, sigungu, dong):
    """카카오맵 API로 매물 주소의 좌표 가져오기"""
    address = f"{sido} {sigungu} {dong}".strip()
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address, "analyze_type": "exact"}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    result = response.json()
    
    if result.get('documents'):
        location = result['documents'][0]
        return {
            'latitude': float(location['y']),
            'longitude': float(location['x'])
        }
    return None

@provide_session
def update_missing_property_coordinates(session=None, batch_size=100):
    """매물 좌표 업데이트"""
    try:
        logger.info("=== 누락된 매물 좌표 업데이트 시작 ===")
        
        # 좌표가 누락된 매물 조회 - CAST 사용
        missing_coords = session.execute(text("""
            SELECT DISTINCT 
                p.property_id,
                p.sido,
                p.sigungu,
                p.dong
            FROM realestate.property_locations p
            WHERE p.latitude IS NULL 
                OR p.longitude IS NULL 
                OR CAST(p.latitude AS TEXT) IN ('', 'nan', 'NaN', 'NULL')
                OR CAST(p.longitude AS TEXT) IN ('', 'nan', 'NaN', 'NULL')
        """)).fetchall()
        
        if not missing_coords:
            logger.info("업데이트할 매물 좌표가 없습니다.")
            return True
            
        logger.info(f"=== 총 {len(missing_coords)}개의 매물 좌표 업데이트 필요 ===")
        
        # 배치 단위로 업데이트
        updated_count = 0
        error_count = 0
        skipped_count = 0
        
        for i in range(0, len(missing_coords), batch_size):
            batch = missing_coords[i:i + batch_size]
            logger.info(f"\n=== 배치 처리 시작: {i//batch_size + 1}/{(len(missing_coords)-1)//batch_size + 1} ===")
            
            for row in batch:
                try:
                    full_address = f"{row[1]} {row[2]} {row[3]}"
                    logger.info(f"\n처리 중: property_id={row[0]}, 주소={full_address}")
                    
                    coords = get_coordinates_from_kakao_for_property(
                        row[1],  # sido
                        row[2],  # sigungu
                        row[3]   # dong
                    )
                    
                    if coords:
                        # updated_at 컬럼 제거
                        session.execute(
                            text("""
                                UPDATE realestate.property_locations
                                SET latitude = :lat,
                                    longitude = :lon
                                WHERE property_id = :prop_id
                            """),
                            {
                                'prop_id': row[0],
                                'lat': coords['latitude'],
                                'lon': coords['longitude']
                            }
                        )
                        session.commit()  # 각 업데이트마다 커밋
                        updated_count += 1
                        logger.info(f"✓ 좌표 업데이트 성공: lat={coords['latitude']}, lon={coords['longitude']}")
                    else:
                        skipped_count += 1
                        logger.warning(f"⚠ 좌표를 찾을 수 없음: {full_address}")
                    
                    if updated_count % 10 == 0:
                        logger.info(f"\n=== 진행 상황 ===")
                        logger.info(f"성공: {updated_count}")
                        logger.info(f"실패: {error_count}")
                        logger.info(f"건너뜀: {skipped_count}")
                        logger.info(f"진행률: {updated_count}/{len(missing_coords)} ({(updated_count/len(missing_coords)*100):.1f}%)")
                    
                    time.sleep(0.1)  # API 호출 제한 준수
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ 오류 발생 (property_id: {row[0]}): {str(e)}")
                    session.rollback()  # 오류 발생 시 롤백
                    continue
        
        logger.info("\n=== 매물 좌표 업데이트 최종 결과 ===")
        logger.info(f"총 처리: {len(missing_coords)}")
        logger.info(f"성공: {updated_count}")
        logger.info(f"실패: {error_count}")
        logger.info(f"건너뜀: {skipped_count}")
        return True
        
    except Exception as e:
        logger.error(f"치명적 오류 발생: {str(e)}")
        session.rollback()
        raise

def update_all_coordinates():
    """주소와 매물의 모든 누락된 좌표 업데이트"""
    try:
        # 먼저 주소 좌표 업데이트
        if update_missing_address_coordinates():
            # 그 다음 매물 좌표 업데이트
            return update_missing_property_coordinates()
        return False
    except Exception as e:
        logger.error(f"좌표 업데이트 중 오류 발생: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # 1. 먼저 주소 좌표 업데이트
        logger.info("1. 주소 좌표 업데이트 시작")
        update_address_coordinates()
        
        # 2. 그 다음 매물 좌표 업데이트
        logger.info("2. 매물 좌표 업데이트 시작")
        update_missing_property_coordinates()
        
        logger.info("모든 좌표 업데이트 완료")
    except Exception as e:
        logger.error(f"좌표 업데이트 중 오류 발생: {str(e)}") 