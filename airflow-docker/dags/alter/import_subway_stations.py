import pandas as pd
from alter.models import Address, SubwayStation
from alter.db_config import provide_session
from alter.utils import main_logger as logger
import os
import logging
from datetime import datetime

@provide_session
def import_subway_stations(session=None):
    """지하철역 데이터 가져오기"""
    try:
        file_path = "/opt/airflow/dags/data/지하철/seoul_subway_stations.csv"
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return
            
        df = pd.read_csv(file_path)
        
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # 주소 처리
                area_name = row['역이름']
                address = session.query(Address).filter_by(area_name=area_name).first()
                
                if not address:
                    now = datetime.now()
                    address = Address(
                        area_name=area_name,
                        latitude=row['위도'],
                        longitude=row['경도'],
                        created_at=now,
                        updated_at=now
                    )
                    session.add(address)
                    session.flush()
                
                # 지하철역 정보 저장
                now = datetime.now()
                subway = SubwayStation(
                    address_id=address.id,
                    line_info=row['설명'],
                    created_at=now
                )
                session.add(subway)
                success_count += 1
                
                if success_count % 10 == 0:  # 10개마다 커밋
                    session.commit()
                    
            except Exception as e:
                error_count += 1
                logger.error(f"행 처리 중 오류 (행 {idx}): {str(e)}")
                session.rollback()
                continue
                
        session.commit()
        logger.info(f"지하철역 데이터 가져오기 완료 - 성공: {success_count}, 실패: {error_count}")
        
    except Exception as e:
        logger.error(f"지하철역 데이터 가져오기 중 오류 발생: {str(e)}")
        session.rollback()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_subway_stations() 