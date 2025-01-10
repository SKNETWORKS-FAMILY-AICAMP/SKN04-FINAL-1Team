from sqlalchemy.orm import Session
from db_config import engine
from alter.models import Address
import requests
import time
from tqdm import tqdm
import json

# 카카오 REST API 키
KAKAO_API_KEY = "2a73d4dd6e7ed9fa4225a757aa5822bb"

def get_coordinates_from_kakao(address):
    """카카오맵 API로 주소의 좌표 가져오기"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": address,
        "analyze_type": "exact"  # 정확히 일치하는 주소 검색
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get('documents'):
            # 첫 번째 결과 사용
            location = result['documents'][0]
            return {
                'latitude': float(location['y']),
                'longitude': float(location['x'])
            }
        return None
        
    except Exception as e:
        print(f"API 요청 실패 ({address}): {str(e)}")
        return None

def update_address_coordinates():
    """좌표가 없는 주소들의 좌표 업데이트"""
    with Session(engine) as session:
        try:
            # 좌표가 없는 주소들 조회
            addresses = session.query(Address).filter(
                (Address.latitude.is_(None)) | 
                (Address.longitude.is_(None))
            ).all()
            
            print(f"좌표가 없는 주소 수: {len(addresses)}")
            
            # 진행 상황 표시
            for address in tqdm(addresses, desc="좌표 업데이트"):
                # 이미 처리된 주소는 건너뛰기
                if address.latitude and address.longitude:
                    continue
                
                # 카카오맵 API로 좌표 가져오기
                coords = get_coordinates_from_kakao(address.area_name)
                
                if coords:
                    address.latitude = coords['latitude']
                    address.longitude = coords['longitude']
                    session.add(address)
                    
                    # 100개마다 커밋
                    if addresses.index(address) % 100 == 0:
                        session.commit()
                        print(f"\n중간 저장 완료: {addresses.index(address)}개")
                
                # API 호출 제한 준수 (초당 10회)
                time.sleep(0.1)
            
            # 남은 변경사항 저장
            session.commit()
            print("\n모든 주소 업데이트 완료!")
            
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            session.rollback()
            raise e

def save_failed_addresses(failed_list):
    """실패한 주소들 저장"""
    with open('failed_addresses.json', 'w', encoding='utf-8') as f:
        json.dump(failed_list, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    update_address_coordinates() 