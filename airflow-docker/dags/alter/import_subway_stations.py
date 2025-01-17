import pandas as pd
from alter.models import Address, SubwayStation
from alter.db_config import provide_session
from alter.utils import main_logger as logger
import os
import logging

@provide_session
def import_subway_stations(session=None):
    """지하철역 데이터 가져오기"""
    try:
        file_path = "/opt/airflow/dags/data/지하철/seoul_subway_stations.csv"
        
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return False
            
        df = pd.read_csv(file_path)
        df['호선정보'] = df['호선정보'].fillna('').apply(lambda x: [line.strip() for line in str(x).split(',')])
        
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # 주소 처리
                area_name = row['역이름']
                address = session.query(Address).filter_by(area_name=area_name).first()
                
                if not address:
                    address = Address(
                        area_name=area_name,
                        latitude=row['위도'],
                        longitude=row['경도']
                    )
                    session.add(address)
                    session.flush()
                
                # 각 호선별로 별도의 레코드 생성
                for line in row['호선정보']:
                    if line:  # 빈 문자열이 아닌 경우만 처리
                        station = SubwayStation(
                            address_id=address.id,  # address.id 사용
                            line_info=line
                        )
                        session.add(station)
                
                success_count += 1
                
                if success_count % 10 == 0:  # 10개마다 커밋
                    session.commit()
                
            except Exception as e:
                error_count += 1
                logger.error(f"행 처리 중 오류 (행 {idx}): {str(e)}")
                session.rollback()
                continue
                
        session.commit()
        logger.info(f"지하철역 데이터 처리 완료 - 성공: {success_count}, 실패: {error_count}")
        return True
        
    except Exception as e:
        logger.error(f"지하철역 데이터 처리 중 오류: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_subway_stations() 