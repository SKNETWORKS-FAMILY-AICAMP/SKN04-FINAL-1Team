import pandas as pd
from alter.models import Address, CulturalFestival
from alter.db_config import provide_session
from alter.utils import main_logger as logger
import os
from datetime import datetime

@provide_session
def import_cultural_festivals(session=None):
    """문화행사 데이터 가져오기"""
    try:
        file_path = "/opt/airflow/dags/data/문화축제/전국 문화축제 데이터.csv"
        
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return False
            
        df = pd.read_csv(file_path)
        
        # 서울 데이터만 필터링
        df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
        
        success_count = 0
        error_count = 0
        
        for idx, row in df.iterrows():
            try:
                # 주소 처리
                area_name = row['RDNMADR_NM']
                address = session.query(Address).filter_by(area_name=area_name).first()
                
                if not address:
                    now = datetime.now()
                    address = Address(
                        area_name=area_name,
                        latitude=row['FCLTY_LA'],
                        longitude=row['FCLTY_LO'],
                        created_at=now,
                        updated_at=now
                    )
                    session.add(address)
                    session.flush()
                
                # 문화행사 정보 저장
                festival = CulturalFestival(
                    address_id=address.id,
                    festival_name=row['FCLTY_NM'],
                    start_date=row['FSTVL_BEGIN_DE'],
                    end_date=row['FSTVL_END_DE'],
                    created_at=datetime.now()
                )
                session.add(festival)
                
                success_count += 1
                
                if success_count % 10 == 0:  # 10개마다 커밋
                    session.commit()
                    
            except Exception as e:
                error_count += 1
                logger.error(f"행 처리 중 오류 (행 {idx}): {str(e)}")
                session.rollback()
                continue
        
        session.commit()
        logger.info(f"문화행사 데이터 처리 완료 - 성공: {success_count}, 실패: {error_count}")
        return True
        
    except Exception as e:
        logger.error(f"문화행사 데이터 처리 중 오류: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    import_cultural_festivals() 