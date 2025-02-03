import pandas as pd
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
from alter.models import Address, CrimeStats
from alter.db_config import provide_session
from alter.utils import main_logger as logger
from airflow.models import Variable

# 서울시 OpenAPI 설정
SEOUL_API_KEY = Variable.get("SEOUL_API_KEY")
API_URL = f"http://openapi.seoul.go.kr:8088/{SEOUL_API_KEY}/xml/SPOP_LOCAL_RESD_JACHI/1/25/"

# 구청 코드와 구 이름 매핑
DISTRICT_CODE_TO_ADDRESS = {
    "11110": "종로구",
    "11140": "중구",
    "11170": "용산구",
    "11200": "성동구",
    "11215": "광진구",
    "11230": "동대문구",
    "11260": "중랑구",
    "11290": "성북구",
    "11305": "강북구",
    "11320": "도봉구",
    "11350": "노원구",
    "11380": "은평구",
    "11410": "서대문구",
    "11440": "마포구",
    "11470": "양천구",
    "11500": "강서구",
    "11530": "구로구",
    "11545": "금천구",
    "11560": "영등포구",
    "11590": "동작구",
    "11620": "관악구",
    "11650": "서초구",
    "11680": "강남구",
    "11710": "송파구",
    "11740": "강동구"
}

def get_district_population(district_code):
    """서울시 생활인구 API에서 구별 인구 데이터 가져오기"""
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            # API 응답 확인
            result_code = root.find('.//CODE').text
            if result_code != 'INFO-000':
                logger.error(f"API 오류: {root.find('.//MESSAGE').text}")
                return None
                
            # 해당 구의 데이터 찾기
            for row in root.findall('.//row'):
                adstrd_code = row.find('ADSTRD_CODE_SE').text[:5]  # 앞 5자리만 사용
                if adstrd_code == district_code:
                    return float(row.find('TOT_LVPOP_CO').text)
        
        return None
    except Exception as e:
        logger.error(f"인구 데이터 가져오기 실패: {str(e)}")
        return None

def process_crime_stats(session, address_id, crime_data):
    """범죄 통계 데이터 처리"""
    try:
        # 범죄 유형별로 카운트를 적절한 컬럼에 매핑
        crime_category = crime_data['crime_category']
        incident_count = crime_data['incident_count']
        
        # 기존 통계 레코드 찾기 또는 새로 생성
        stats = session.query(CrimeStats).filter_by(
            address_id=address_id,
            reference_date=crime_data.get('reference_date')
        ).first()
        
        if not stats:
            stats = CrimeStats(
                address_id=address_id,
                reference_date=crime_data.get('reference_date'),
                total_crime_count=0,
                violent_crime_count=0,
                theft_crime_count=0,
                intellectual_crime_count=0,
                created_at=datetime.now()  # created_at 필드 명시적 설정
            )
            session.add(stats)
        
        # 범죄 대분류에 따라 적절한 카운트 업데이트
        if crime_category == '폭력범죄':
            stats.violent_crime_count += incident_count
        elif crime_category == '절도범죄':
            stats.theft_crime_count += incident_count
        elif crime_category == '지능범죄':
            stats.intellectual_crime_count += incident_count
            
        # 전체 범죄 건수 업데이트
        stats.total_crime_count = (
            stats.violent_crime_count +
            stats.theft_crime_count +
            stats.intellectual_crime_count
        )
        
        session.flush()
        return stats
    except Exception as e:
        logger.error(f"범죄 통계 처리 중 오류: {str(e)}")
        session.rollback()
        return None

def calculate_crime_rate(incident_count, population):
    """인구 10만명당 범죄 발생률 계산"""
    try:
        if population and population > 0:
            return (float(incident_count) / float(population)) * 100000
        return None
    except Exception as e:
        logger.error(f"범죄율 계산 중 오류: {str(e)}")
        return None

def get_or_create_address(session, area_name):
    """주소 가져오기 또는 생성"""
    address = session.query(Address).filter_by(area_name=area_name).first()
    if not address:
        now = datetime.now()
        address = Address(
            area_name=area_name,
            latitude=None,  # 나중에 update_address_coordinates.py에서 업데이트됨
            longitude=None,
            created_at=now,
            updated_at=now
        )
        session.add(address)
        session.flush()
        logger.info(f"새 주소 생성됨: {area_name}")
    return address

@provide_session
def import_crime_stats(session=None):
    """범죄 통계 데이터 가져오기"""
    try:
        file_path = "/opt/airflow/dags/data/범죄율/서울시_범죄_통계.csv"
        
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return False
            
        df = pd.read_csv(file_path, encoding='utf-8')
        
        logger.info(f"데이터프레임 컬럼: {df.columns.tolist()}")
        
        starred_crimes = [
            '살인기수', '살인미수등', '강도', '강간', '유사강간',
            '강제추행', '기타 강간 강제추행등', '상해', '폭행', '협박', 
            '폭력행위등', '손괴', '사기'
        ]
        
        success_count = 0
        error_count = 0
        
        districts = [col for col in df.columns if '서울' in col]
        logger.info(f"처리할 구: {districts}")
        
        for district in districts:
            district_name = district.replace('서울', '').strip()
            logger.info(f"처리 중인 구: {district_name}")
            
            district_code = next((code for code, name in DISTRICT_CODE_TO_ADDRESS.items() 
                                if name == district_name), None)
            
            if district_code is None:
                logger.warning(f"구 코드를 찾을 수 없음: {district_name}")
                continue
            
            total_population = get_district_population(district_code)
            logger.info(f"{district_name} 인구: {total_population}")
            
            area_name = f"서울특별시 {district_name}"
            address = get_or_create_address(session, area_name)
            
            for crime_type in starred_crimes:
                try:
                    crime_rows = df[df['범죄중분류'] == crime_type]
                    if crime_rows.empty:
                        logger.warning(f"범죄 유형 찾을 수 없음: {crime_type}")
                        continue
                        
                    crime_count = int(crime_rows[district].iloc[0])
                    crime_category = crime_rows['범죄대분류'].iloc[0]
                    
                    crime_data = {
                        'area_name': area_name,
                        'reference_date': datetime.now().strftime('%Y%m%d'),
                        'total_population': total_population,
                        'crime_category': crime_category,
                        'crime_subcategory': crime_type,
                        'incident_count': crime_count
                    }
                    
                    if process_crime_stats(session, address.id, crime_data):
                        success_count += 1
                        if success_count % 10 == 0:
                            session.commit()
                    else:
                        error_count += 1
                    
                except Exception as e:
                    logger.error(f"데이터 처리 중 오류: {str(e)}")
                    error_count += 1
                    continue
        
        session.commit()
        logger.info(f"범죄 통계 가져오기 완료 - 성공: {success_count}, 실패: {error_count}")
        return True
        
    except Exception as e:
        logger.error(f"범죄 통계 가져오기 실패: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    import_crime_stats() 