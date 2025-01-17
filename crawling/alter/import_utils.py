from sqlalchemy.orm import Session
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 모델 임포트
from models import (
    Address, 
    SubwayStation, 
    CulturalFacility, 
    CulturalFestival, 
    CrimeStats, 
    PopulationStats,
)
# 유틸 임포트
from db_config import engine
import logging

logger = logging.getLogger(__name__)

def get_or_create_address(session, area_name=None, latitude=None, longitude=None):
    """주소 데이터를 가져오거나 생성"""
    try:
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
        
        # 주소 검색 조건
        conditions = []
        
        if area_name:
            conditions.append(Address.area_name == area_name)
            
            # 좌표가 없는 경우 매핑된 좌표 사용
            if (not latitude or not longitude or pd.isna(latitude) or pd.isna(longitude)):
                for location, coords in LOCATION_COORDINATES.items():
                    if location in area_name:
                        latitude, longitude = coords
                        break
                        
        if latitude and longitude and not pd.isna(latitude) and not pd.isna(longitude):
            conditions.extend([
                Address.latitude == float(latitude),
                Address.longitude == float(longitude)
            ])
        
        # 기존 주소 검색
        if conditions:
            address = session.query(Address).filter(*conditions).first()
        else:
            address = None
        
        if not address:
            # 새 주소 생성
            address = Address(
                area_name=area_name,
                latitude=float(latitude) if latitude and not pd.isna(latitude) else None,
                longitude=float(longitude) if longitude and not pd.isna(longitude) else None
            )
            session.add(address)
            session.flush()
            logger.info(f"새 주소 생성: {area_name} ({address.latitude}, {address.longitude})")
        else:
            # 기존 주소에 좌표가 없는 경우 업데이트
            if (not address.latitude or not address.longitude) and latitude and longitude:
                address.latitude = float(latitude)
                address.longitude = float(longitude)
                session.add(address)
                logger.info(f"주소 좌표 업데이트: {area_name} ({latitude}, {longitude})")
            else:
                logger.info(f"기존 주소 사용: {area_name}")
        
        return address
        
    except Exception as e:
        logger.error(f"주소 처리 중 오류: {str(e)}")
        raise e

def import_with_address(process_func):
    """주소 처리를 포함한 데이터 임포트 데코레이터"""
    def decorator(import_func):
        def wrapper(session, *args, **kwargs):  # session 파라미터 추가
            try:
                logger.info(f"\n=== {import_func.__name__} 시작 ===")
                data = import_func(*args, **kwargs)  # session 제외하고 나머지 인자만 전달
                logger.info(f"데이터 로드 완료: {len(data)}개")
                
                processed_count = 0
                error_count = 0
                batch = []
                
                for idx, item in enumerate(data, 1):
                    try:
                        # 주소 처리
                        address = get_or_create_address(session, area_name=item.get('area_name'))
                        if not address:
                            continue
                            
                        # 모델 인스턴스 생성
                        model_instance = process_func(session, item)
                        if model_instance:
                            batch.append(model_instance)
                            processed_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        logger.error(f"처리 실패 ({idx}/{len(data)}): {str(e)}")
                        continue
                
                # 배치 처리
                if batch:
                    session.bulk_save_objects(batch)
                    session.commit()
                
                logger.info(f"\n=== {import_func.__name__} 완료 ===")
                logger.info(f"성공: {processed_count}개")
                logger.info(f"실패: {error_count}개")
                
            except Exception as e:
                session.rollback()
                raise e
                
        return wrapper
    return decorator

def process_subway_data(session, item):
    """지하철역 데이터 처리"""
    try:
        area_name = item.get('area_name')
        if not area_name:
            return None
            
        # 주소 처리
        address = get_or_create_address(
            session,
            area_name=area_name
        )
        
        # SubwayStation 객체 생성
        station = SubwayStation(
            address_id=address.address_id,
            line_info=item.get('line_info')
        )
        
        session.add(station)
        session.flush()
        return station
        
    except Exception as e:
        logger.error(f"지하철역 처리 오류: {str(e)}")
        return None

def process_cultural_facility_data(session, item):
    """문화시설 데이터 처리"""
    try:
        facility_name = item.get('facility_name')
        if not facility_name:
            return None
            
        # 주소 처리
        address = get_or_create_address(
            session,
            area_name=item.get('area_name'),
            latitude=item.get('FCLTY_LA'),  # 위도
            longitude=item.get('FCLTY_LO')  # 경도
        )
        
        # 문화시설 객체 생성
        facility = CulturalFacility(
            facility_name=facility_name,
            facility_type=item.get('facility_type'),
            address_id=address.address_id
        )
        
        session.add(facility)
        session.flush()
        return facility
        
    except Exception as e:
        logger.error(f"문화시설 처리 오류: {str(e)}")
        return None

def process_festival_data(session, item):
    """문화축제 데이터 처리"""
    try:
        festival_name = item.get('festival_name')
        if not festival_name:
            return None
            
        # 주소 처리
        address = get_or_create_address(
            session,
            area_name=item.get('area_name'),
            latitude=item.get('FCLTY_LA'),
            longitude=item.get('FCLTY_LO')
        )
        
        # 축제 객체 생성
        festival = CulturalFestival(
            festival_name=festival_name,
            address_id=address.address_id,
            begin_date=item.get('begin_date'),
            end_date=item.get('end_date')
        )
        
        session.add(festival)
        session.flush()
        return festival
        
    except Exception as e:
        logger.error(f"축제 처리 오류: {str(e)}")
        return None

def process_crime_stats_data(session, item):
    """범죄 통계 데이터 처리"""
    try:
        # 주소 처리
        address = get_or_create_address(
            session,
            area_name=item.get('area_name'),
            latitude=item.get('latitude'),
            longitude=item.get('longitude')
        )
        
        # 범죄 통계 객체 생성
        stats = CrimeStats(
            crime_category=item.get('crime_category'),
            crime_subcategory=item.get('crime_subcategory'),
            incident_count=item.get('incident_count'),
            address_id=address.address_id
        )
        
        session.add(stats)
        session.flush()
        return stats
        
    except Exception as e:
        logger.error(f"범죄 통계 처리 오류: {str(e)}")
        return None

def process_population_data(db, address_id, data):
    """유동인구 데이터 처리"""
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
    db.add(stats)
    return stats

def get_data_by_address(session, address_id, model_class):
    """주소 ID로 데이터 조회"""
    return session.query(model_class).filter_by(address_id=address_id).all()

def get_all_data_with_address():
    """모든 데이터를 주소 정보와 함께 조회"""
    with Session(engine) as session:
        try:
            # 모든 주소 조회
            addresses = session.query(Address).all()
            result = []
            
            for address in addresses:
                address_data = {
                    'address_id': address.address_id,
                    'sido': address.sido,
                    'sigungu': address.sigungu,
                    'dong': address.dong,
                    'detail_address': address.detail_address,
                    'latitude': address.latitude,
                    'longitude': address.longitude,
                    'created_at': address.created_at,
                    'facilities': [
                        {
                            'facility_id': f.facility_id,
                            'facility_name': f.facility_name,
                            'category': f.category,
                            'contact': f.contact,
                            'description': f.description,
                            'latitude': f.latitude,
                            'longitude': f.longitude,
                            'created_at': f.created_at
                        }
                        for f in address.cultural_facilities
                    ],
                    'festivals': [
                        {
                            'festival_id': f.festival_id,
                            'festival_name': f.festival_name,
                            'category': f.category,
                            'start_date': f.start_date,
                            'end_date': f.end_date,
                            'host': f.host,
                            'contact': f.contact,
                            'homepage': f.homepage,
                            'description': f.description,
                            'fee_info': f.fee_info,
                            'latitude': f.latitude,
                            'longitude': f.longitude,
                            'created_at': f.created_at
                        }
                        for f in address.cultural_festivals
                    ],
                    'subway_stations': [
                        {
                            'station_id': s.station_id,
                            'station_name': s.station_name,
                            'description': s.description,
                            'region': s.region,
                            'line_info': s.line_info,
                            'latitude': s.latitude,
                            'longitude': s.longitude,
                            'created_at': s.created_at
                        }
                        for s in address.subway_stations
                    ],
                    'crime_stats': [
                        {
                            'id': c.id,
                            'district': c.district,
                            'year': c.year,
                            'total_crimes': c.total_crimes,
                            'crime_rate': c.crime_rate,
                            'created_at': c.created_at
                        }
                        for c in address.crime_stats
                    ],
                    'population_stats': [
                        {
                            'id': p.id,
                            'area_code': p.area_code,
                            'area_name': p.area_name,
                            'collection_time': p.collection_time,
                            'population_level': p.population_level,
                            'population_message': p.population_message,
                            'min_population': p.min_population,
                            'max_population': p.max_population,
                            'male_ratio': p.male_ratio,
                            'female_ratio': p.female_ratio,
                            'age_0_9_ratio': p.age_0_9_ratio,
                            'age_10s_ratio': p.age_10s_ratio,
                            'age_20s_ratio': p.age_20s_ratio,
                            'age_30s_ratio': p.age_30s_ratio,
                            'age_40s_ratio': p.age_40s_ratio,
                            'age_50s_ratio': p.age_50s_ratio,
                            'age_60s_ratio': p.age_60s_ratio,
                            'age_70s_ratio': p.age_70s_ratio,
                            'resident_ratio': p.resident_ratio,
                            'non_resident_ratio': p.non_resident_ratio,
                            'created_at': p.created_at
                        }
                        for p in address.population_stats
                    ]
                }
                result.append(address_data)
            
            return result
            
        except Exception as e:
            logger.error(f"데이터 조회 중 오류 발생: {str(e)}")
            raise e 


def get_address_by_location(session, sigungu=None, dong=None):
    """위치 정보로 주소 조회"""
    query = session.query(Address).filter(Address.sido == '서울특별시')
    
    if sigungu:
        query = query.filter(Address.sigungu == sigungu)
    if dong:
        query = query.filter(Address.dong == dong)
    
    return query.first()

def extract_address_info(data_type, item):
    """각 데이터 소스별 주소 정보 추출"""
    try:
        if data_type == 'cultural_facility':
            # 나혼자, 실내놀이, 실외놀이 문화시설
            if 'FCLTY_ROAD_NM_ADDR' in item:
                if not item['CTPRVN_NM'] == '서울특별시':
                    return None
                    
                address = item['FCLTY_ROAD_NM_ADDR']
                latitude = float(item['FCLTY_LA']) if pd.notna(item.get('FCLTY_LA')) else None
                longitude = float(item['FCLTY_LO']) if pd.notna(item.get('FCLTY_LO')) else None
                sigungu = item.get('SIGNGU_NM')
                dong = item.get('LEGALDONG_NM')
                
            # 영화관, 전시관
            elif 'POI_NM' in item:
                if not item['CTPRVN_NM'] == '서울특별시':
                    return None
                    
                address = f"{item['RDNMADR_NM']} {item.get('BULD_NO', '')}"
                latitude = float(item['LC_LA']) if pd.notna(item.get('LC_LA')) else None
                longitude = float(item['LC_LO']) if pd.notna(item.get('LC_LO')) else None
                sigungu = item.get('SIGNGU_NM')
                dong = item.get('LEGALDONG_NM')
            
        elif data_type == 'festival':
            if not item['CTPRVN_NM'] == '서울특별시':
                return None
                
            address = item.get('RDNMADR_NM')
            latitude = float(item['FCLTY_LA']) if pd.notna(item.get('FCLTY_LA')) else None
            longitude = float(item['FCLTY_LO']) if pd.notna(item.get('FCLTY_LO')) else None
            sigungu = item.get('SIGNGU_NM')
            dong = item.get('LEGALDONG_NM')
            
        elif data_type == 'subway':
            address = item.get('역이름')
            latitude = float(item['위도']) if pd.notna(item.get('위도')) else None
            longitude = float(item['경도']) if pd.notna(item.get('경도')) else None
            sigungu = item.get('지하철권역')
            dong = None
            
        elif data_type == 'crime':
            address = item.get('district')
            latitude = None
            longitude = None
            sigungu = item.get('district')
            dong = None
            
        elif data_type == 'population':
            address = item.get('지역명')
            latitude = None
            longitude = None
            sigungu = next((part for part in address.split() if '구' in part), None)
            dong = None
            
        else:
            return None
            
        # 주소 정보 반환 (구 정보가 없어도 됨)
        return {
            'sido': '서울특별시',
            'sigungu': sigungu,  # None이어도 됨
            'dong': dong,
            'detail_address': address,
            'latitude': latitude,
            'longitude': longitude
        }
        
    except Exception as e:
        logger.error(f"주소 정보 추출 중 오류: {str(e)}")
        logger.error(f"데이터 타입: {data_type}")
        logger.error(f"데이터: {item}")
        return None

def create_addresses_from_all_sources(session):
    """모든 데이터 소스에서 주소 추출 및 생성"""
    addresses = []
    
    # 1. 문화시설 데이터에서 주소 추출
    facility_files = [
        '나혼자 문화시설 데이터.csv',
        '아이랑 실내 놀이 시설 데이터.csv',
        '아이랑 실외 놀이 시설 데이터.csv',
        '전국 영화관 시설 데이터.csv',
        '전국 전시관 데이터.csv'
    ]
    
    for filename in facility_files:
        try:
            df = pd.read_csv(f'../data/문화시설/{filename}')
            # 서울 데이터만 필터링
            df = df[df['CTPRVN_NM'] == '서울특별시']
            
            for _, row in df.iterrows():
                area_name = f"서울특별시 {row['FCLTY_ROAD_NM_ADDR']}"
                latitude = float(row['FCLTY_LA']) if 'FCLTY_LA' in row and pd.notna(row['FCLTY_LA']) else \
                          float(row['LC_LA']) if 'LC_LA' in row and pd.notna(row['LC_LA']) else None
                longitude = float(row['FCLTY_LO']) if 'FCLTY_LO' in row and pd.notna(row['FCLTY_LO']) else \
                           float(row['LC_LO']) if 'LC_LO' in row and pd.notna(row['LC_LO']) else None
                
                try:
                    address = get_or_create_address(
                        session,
                        area_name=area_name,
                        latitude=latitude,
                        longitude=longitude
                    )
                    addresses.append(address)
                except Exception as e:
                    logger.error(f"주소 저장 중 오류: {str(e)}")
                    continue
                    
        except Exception as e:
            print(f"파일 처리 중 오류 ({filename}): {str(e)}")
            continue
    
    # 2. 문화축제 데이터에서 주소 추출
    try:
        df = pd.read_csv('../data/문화축제/전국 문화축제 데이터.csv')
        df = df[df['CTPRVN_NM'] == '서울특별시']
        
        for _, row in df.iterrows():
            area_name = f"서울특별시 {row['RDNMADR_NM']}"
            latitude = float(row['FCLTY_LA']) if pd.notna(row['FCLTY_LA']) else None
            longitude = float(row['FCLTY_LO']) if pd.notna(row['FCLTY_LO']) else None
            
            try:
                address = get_or_create_address(
                    session,
                    area_name=area_name,
                    latitude=latitude,
                    longitude=longitude
                )
                addresses.append(address)
            except Exception as e:
                logger.error(f"주소 저장 중 오류: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"문화축제 데이터 처리 중 오류: {str(e)}")
    
    # 3. 지하철역 데이터에서 주소 추출
    try:
        df = pd.read_csv('./data/지하철/seoul_subway_stations.csv')
        for _, row in df.iterrows():
            area_name = row['역이름']  # 역 이름을 area_name으로 사용
            latitude = float(row['위도']) if pd.notna(row['위도']) else None
            longitude = float(row['경도']) if pd.notna(row['경도']) else None
            
            try:
                address = get_or_create_address(
                    session,
                    area_name=area_name,
                    latitude=latitude,
                    longitude=longitude
                )
                addresses.append(address)
            except Exception as e:
                logger.error(f"주소 저장 중 오류: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"지하철역 데이터 처리 중 오류: {str(e)}")
    
    # 중복 제거 및 저장
    unique_addresses = list(set(addresses))
    session.commit()
    logger.info(f"\n총 {len(unique_addresses)}개의 주소 생성 완료")
    return unique_addresses 

def create_engine_and_session():
    """데이터베이스 엔진과 세션을 생성합니다."""
    # SQLite 데이터베이스 연결
    engine = create_engine(
        'sqlite:///real_estate.db',
        isolation_level='IMMEDIATE',
        echo=False,  # SQL 로깅 비활성화
        connect_args={
            'timeout': 30,
            'check_same_thread': False
        }
    )
    
    # 세션 팩토리 생성
    Session = sessionmaker(bind=engine)
    
    # 세션 생성
    session = Session()
    
    return engine, session 

def process_cultural_festival_data(session, item):
    """문화축제 데이터 처리"""
    try:
        festival_name = item.get('festival_name')
        if not festival_name:
            return None
            
        # 주소 처리
        address = get_or_create_address(
            session,
            area_name=item.get('area_name'),
            latitude=item.get('FCLTY_LA'),  # 위도
            longitude=item.get('FCLTY_LO')  # 경도
        )
        
        # 문화축제 객체 생성
        festival = CulturalFestival(
            festival_name=festival_name,
            address_id=address.address_id,
            begin_date=item.get('begin_date'),
            end_date=item.get('end_date')
        )
        
        session.add(festival)
        session.flush()
        return festival
        
    except Exception as e:
        logger.error(f"문화축제 처리 오류: {str(e)}")
        return None
