import pandas as pd
from alter.models import Address, CulturalFacility
from alter.db_config import provide_session
from alter.utils import main_logger as logger
import os
import logging

@provide_session
def import_cultural_facilities(session=None):
    """문화시설 데이터 가져오기"""
    try:
        base_path = "/opt/airflow/dags/data/문화시설"
        
        # 1. 기본 문화시설 (나혼자, 실내놀이, 실외놀이)
        facility_files = [
            '나혼자 문화시설 데이터.csv',
            '아이랑 실내 놀이 시설 데이터.csv',
            '아이랑 실외 놀이 시설 데이터.csv'
        ]
        
        success_count = 0
        error_count = 0
        
        for file_name in facility_files:
            file_path = os.path.join(base_path, file_name)
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않습니다: {file_path}")
                continue
                
            try:
                df = pd.read_csv(file_path)
                # 서울 데이터만 필터링
                df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
                
                for _, row in df.iterrows():
                    try:
                        # 주소 처리
                        area_name = row['FCLTY_ROAD_NM_ADDR']
                        address = session.query(Address).filter_by(area_name=area_name).first()
                        
                        if not address:
                            address = Address(
                                area_name=area_name,
                                latitude=row['FCLTY_LA'],
                                longitude=row['FCLTY_LO']
                            )
                            session.add(address)
                            session.flush()
                        
                        # 문화시설 정보 저장
                        facility = CulturalFacility(
                            address_id=address.id,
                            facility_name=row['FCLTY_NM'],
                            facility_type=row['MLSFC_NM']
                        )
                        session.add(facility)
                        success_count += 1
                        
                        if success_count % 10 == 0:  # 10개마다 커밋
                            session.commit()
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"행 처리 중 오류: {str(e)}")
                        session.rollback()
                        continue
                        
            except Exception as e:
                logger.error(f"파일 처리 중 오류 ({file_name}): {str(e)}")
                continue
        
        # 2. 영화관, 전시관
        other_files = [
            '전국 영화관 시설 데이터.csv',
            '전국 전시관 데이터.csv'
        ]
        
        for file_name in other_files:
            file_path = os.path.join(base_path, file_name)
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않습니다: {file_path}")
                continue
                
            try:
                df = pd.read_csv(file_path)
                # 서울 데이터만 필터링
                df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
                
                for _, row in df.iterrows():
                    try:
                        # 도로명주소와 건물번호 합치기
                        if pd.isna(row.get('RDNMADR_NM')):
                            # 지번 주소 사용
                            full_address = f"{row['SIGNGU_NM']} {row['LEGALDONG_NM']}"
                            if pd.notna(row.get('LNM_ADDR')):
                                full_address += f" {row['LNM_ADDR']}"
                        else:
                            full_address = row['RDNMADR_NM']
                            if pd.notna(row.get('BULD_NO')):
                                full_address = f"{row['RDNMADR_NM']} {row['BULD_NO']}"
                        
                        # POI_NM과 BHF_NM 합치기
                        if pd.isna(row.get('POI_NM')):
                            continue
                            
                        facility_name = row['POI_NM']
                        if pd.notna(row.get('BHF_NM')):
                            facility_name = f"{row['POI_NM']} {row['BHF_NM']}"
                        
                        # 주소 처리
                        address = session.query(Address).filter_by(area_name=full_address).first()
                        
                        if not address:
                            address = Address(
                                area_name=full_address,
                                latitude=row.get('LC_LA', row.get('FCLTY_LA')),
                                longitude=row.get('LC_LO', row.get('FCLTY_LO'))
                            )
                            session.add(address)
                            session.flush()
                        
                        # 문화시설 정보 저장
                        facility = CulturalFacility(
                            address_id=address.id,
                            facility_name=facility_name,
                            facility_type=row.get('CL_NM', '기타')
                        )
                        session.add(facility)
                        success_count += 1
                        
                        if success_count % 10 == 0:
                            session.commit()
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"행 처리 중 오류: {str(e)}")
                        session.rollback()
                        continue
                        
            except Exception as e:
                logger.error(f"파일 처리 중 오류 ({file_name}): {str(e)}")
                continue
        
        session.commit()
        logger.info(f"문화시설 데이터 처리 완료 - 성공: {success_count}, 실패: {error_count}")
        return True
        
    except Exception as e:
        logger.error(f"문화시설 데이터 처리 중 오류: {str(e)}")
        session.rollback()
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import_cultural_facilities() 