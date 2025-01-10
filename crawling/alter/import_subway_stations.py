import pandas as pd
import logging

# 모델 임포트
from models import Address, SubwayStation
# 유틸 임포트
from db_config import SessionLocal

logger = logging.getLogger(__name__)

def get_or_create_address(session, area_name, latitude=None, longitude=None):
    """주소 가져오기 또는 생성, 좌표가 없는 경우 업데이트"""
    try:
        address = session.query(Address).filter_by(area_name=area_name).first()
        if address:
            # 기존 주소가 있고 좌표가 비어있는 경우 업데이트
            if (address.latitude is None or address.longitude is None) and (latitude is not None and longitude is not None):
                address.latitude = latitude
                address.longitude = longitude
                session.flush()
                logger.info(f"기존 주소 좌표 업데이트: {area_name} ({latitude}, {longitude})")
            else:
                logger.info(f"기존 주소 사용: {area_name} ({address.latitude}, {address.longitude})")
        else:
            # 새 주소 생성
            address = Address(
                area_name=area_name,
                latitude=latitude,
                longitude=longitude
            )
            session.add(address)
            session.flush()
            logger.info(f"새 주소 생성됨: {area_name} ({latitude}, {longitude})")
        return address
    except Exception as e:
        logger.error(f"주소 처리 중 오류: {str(e)}")
        return None

def process_subway_data(session, address_id, data):
    """지하철역 데이터 처리"""
    try:
        station = SubwayStation(
            address_id=address_id,
            line_info=data['line_info']
        )
        session.add(station)
        return station
    except Exception as e:
        logger.error(f"지하철역 데이터 처리 중 오류: {str(e)}")
        return None

def import_subway_stations(session):
    """지하철역 데이터 가져오기"""
    try:
        df = pd.read_csv('./data/지하철/seoul_subway_stations.csv')
        
        # 호선 정보를 리스트로 변환
        df['호선정보'] = df['호선정보'].fillna('').apply(lambda x: [line.strip() for line in str(x).split(',')])
        
        success_count = 0
        fail_count = 0
        
        for _, row in df.iterrows():
            try:
                area_name = row['역이름']
                latitude = row['위도']
                longitude = row['경도']
                
                # 주소 가져오기 또는 생성 (좌표 포함)
                address = get_or_create_address(session, area_name, latitude, longitude)
                
                if address:
                    # 각 호선별로 별도의 레코드 생성
                    for line in row['호선정보']:
                        if line:  # 빈 문자열이 아닌 경우만 처리
                            station_data = {
                                'line_info': line.strip()
                            }
                            
                            if process_subway_data(session, address.address_id, station_data):
                                success_count += 1
                                if success_count % 10 == 0:
                                    session.commit()
                            else:
                                fail_count += 1
                                
            except Exception as e:
                logger.error(f"역 데이터 처리 중 오류: {str(e)}")
                fail_count += 1
        
        session.commit()
        logger.info(f"지하철역 데이터 가져오기 완료 - 성공: {success_count}, 실패: {fail_count}")
        
    except Exception as e:
        logger.error(f"지하철역 데이터 가져오기 실패: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    session = SessionLocal()
    try:
        import_subway_stations(session)
    except Exception as e:
        logger.error("메인 실행 중 오류 발생", exc_info=True)
    finally:
        session.close() 