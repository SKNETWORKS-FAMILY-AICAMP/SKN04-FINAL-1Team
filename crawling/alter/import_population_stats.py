import pandas as pd
import os
import logging
from datetime import datetime

# 모델 임포트
from models import PopulationStats, Address

logger = logging.getLogger(__name__)

# 주요 장소 좌표 매핑
LOCATION_COORDINATES = {
    '경복궁': (37.579617, 126.977041),
    'N서울타워': (37.551169, 126.988227),
    '북촌한옥마을': (37.582604, 126.983998),
    '청계천': (37.568267, 126.977831),
    '홍대': (37.556013, 126.923654),
    '창덕궁': (37.582604, 126.991987),
    '광화문': (37.575936, 126.976849),
    '명동': (37.560989, 126.986325),
    '명동성당': (37.563646, 126.987997),
    '수원화성': (37.288071, 127.015202),
    '국립중앙박물관': (37.523344, 126.980960),
    '이화동 벽화마을': (37.576481, 127.001349),
    '코엑스몰': (37.512623, 127.059096),
    '삼청각': (37.606484, 127.002622),
    '노량진수산시장': (37.510297, 126.940808),
    '남산공원': (37.550925, 126.990455),
    '잠실야구장': (37.512086, 127.070376),
    '국립민속박물관': (37.581093, 126.978572),
    '롯데월드': (37.511074, 127.098019),
    '서울어린이대공원': (37.548014, 127.074658),
    '종묘': (37.572441, 126.991015),
    '전쟁기념관': (37.536289, 126.977041),
    '북한산': (37.658359, 126.988201),
    '덕수궁': (37.565804, 126.975144),
    '조계사': (37.571634, 126.981649),
    '봉은사': (37.514032, 127.057942),
    '삼성미술관 리움': (37.539289, 126.994552),
    '창경궁': (37.578608, 126.995340),
    '흥인지문': (37.571424, 127.009745),
    '동대문시장': (37.570004, 127.009512),
    '롯데마트 서울역점': (37.554648, 126.969837),
    '쌈지길': (37.574025, 126.985302),
    '삼청동 거리': (37.584126, 126.981719),
    '반포한강공원': (37.508132, 126.995608),
    '신사동 가로수길': (37.521902, 127.023604),
    '서울숲': (37.544541, 127.037824),
    '뮤지엄 김치간': (37.574025, 126.985302),
    '명동난타극장': (37.563649, 126.985571)
}

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
            # 좌표 가져오기 (LOCATION_COORDINATES에서 먼저 확인)
            if latitude is None or longitude is None:
                coords = LOCATION_COORDINATES.get(area_name)
                if coords:
                    latitude, longitude = coords

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

def process_population_data(session, address_id, data):
    """유동인구 데이터 처리"""
    try:
        stats = PopulationStats(
            address_id=address_id,
            collection_time=datetime.strptime(data['데이터 수집 시간'], '%Y-%m-%d %H:%M'),
            population_level=data['실시간 인구 수준'],
            population_message=data['실시간 인구 메시지'],
            min_population=data['인구 최소값'],
            max_population=data['인구 최대값'],
            male_ratio=data['남성 비율'],
            female_ratio=data['여성 비율'],
            age_0_9_ratio=data['0-9세 비율'],
            age_10s_ratio=data['10대 비율'],
            age_20s_ratio=data['20대 비율'],
            age_30s_ratio=data['30대 비율'],
            age_40s_ratio=data['40대 비율'],
            age_50s_ratio=data['50대 비율'],
            age_60s_ratio=data['60대 비율'],
            age_70s_ratio=data['70대 이상 비율'],
            resident_ratio=data['거주인구 비율'],
            non_resident_ratio=data['비거주인구 비율']
        )
        session.add(stats)
        return stats
    except Exception as e:
        logger.error(f"유동인구 데이터 처리 중 오류: {str(e)}")
        return None

def import_population_stats(session):
    """유동인구 데이터 가져오기"""
    try:
        data_dir = './data/유동인구'
        success_count = 0
        fail_count = 0
        
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                try:
                    file_path = os.path.join(data_dir, filename)
                    df = pd.read_csv(file_path)
                    
                    for _, row in df.iterrows():
                        try:
                            area_name = row['지역명']
                            
                            # 주소 가져오기 또는 생성
                            address = get_or_create_address(session, area_name)
                            
                            population_data = {
                                '데이터 수집 시간': row['데이터 수집 시간'],
                                '실시간 인구 수준': row['실시간 인구 수준'],
                                '실시간 인구 메시지': row['실시간 인구 메시지'],
                                '인구 최소값': row['인구 최소값'],
                                '인구 최대값': row['인구 최대값'],
                                '남성 비율': row['남성 비율'],
                                '여성 비율': row['여성 비율'],
                                '0-9세 비율': row['0-9세 비율'],
                                '10대 비율': row['10대 비율'],
                                '20대 비율': row['20대 비율'],
                                '30대 비율': row['30대 비율'],
                                '40대 비율': row['40대 비율'],
                                '50대 비율': row['50대 비율'],
                                '60대 비율': row['60대 비율'],
                                '70대 이상 비율': row['70대 이상 비율'],
                                '거주인구 비율': row['거주인구 비율'],
                                '비거주인구 비율': row['비거주인구 비율']
                            }
                            
                            if process_population_data(session, address.address_id, population_data):
                                success_count += 1
                                if success_count % 10 == 0:
                                    session.commit()
                            else:
                                fail_count += 1
                                
                        except Exception as e:
                            logger.error(f"데이터 처리 중 오류: {str(e)}")
                            fail_count += 1
                            
                except Exception as e:
                    logger.error(f"{filename} 처리 중 오류 발생: {str(e)}")
                    continue
        
        session.commit()
        logger.info(f"유동인구 데이터 가져오기 완료 - 성공: {success_count}, 실패: {fail_count}")
        
    except Exception as e:
        logger.error(f"유동인구 데이터 가져오기 실패: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    from db_config import SessionLocal
    from alter.models import Address
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    session = SessionLocal()
    try:
        import_population_stats(session)
    except Exception as e:
        logger.error("메인 실행 중 오류 발생", exc_info=True)
    finally:
        session.close() 