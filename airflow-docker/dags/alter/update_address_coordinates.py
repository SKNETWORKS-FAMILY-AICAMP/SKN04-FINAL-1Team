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

@retry_on_failure(max_attempts=3)
def get_coordinates_from_kakao(address):
    """카카오맵 API로 주소의 좌표 가져오기"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {get_api_key('KAKAO_API_KEY')}"}
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
def update_address_coordinates(session=None, batch_size=100):
    """좌표가 없는 주소들의 좌표 업데이트"""
    try:
        addresses = session.query(Address).filter(
            (Address.latitude.is_(None)) | 
            (Address.longitude.is_(None))
        ).all()
        
        logger.info(f"좌표가 없는 주소 수: {len(addresses)}")
        
        stats = {'success': 0, 'error': 0}
        
        for address in tqdm(addresses, desc="좌표 업데이트"):
            try:
                if address.latitude and address.longitude:
                    continue
                
                coords = get_coordinates_from_kakao(address.area_name)
                if coords:
                    address.latitude = coords['latitude']
                    address.longitude = coords['longitude']
                    session.add(address)
                    stats['success'] += 1
                    
                    if stats['success'] % batch_size == 0:
                        session.commit()
                        logger.info(f"중간 저장 완료: {stats['success']}개")
                else:
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
        raise

def save_failed_addresses(failed_list):
    """실패한 주소들 저장"""
    with open('failed_addresses.json', 'w', encoding='utf-8') as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)

class AddressCoordinateUpdater:
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
        self.stats = {'success': 0, 'error': 0}

    @retry_on_failure(max_attempts=3)
    def _update_single_address(self, address, session):
        if address.latitude and address.longitude:
            return

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

if __name__ == "__main__":
    update_address_coordinates() 