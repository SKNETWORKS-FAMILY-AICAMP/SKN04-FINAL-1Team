import os
import pandas as pd
import logging
from import_utils import import_with_address, process_cultural_festival_data

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@import_with_address(process_cultural_festival_data)
def import_cultural_festivals():
    """문화축제 데이터 가져오기"""
    try:
        # 현재 디렉토리 확인
        current_dir = os.getcwd()
        file_path = os.path.join(current_dir, 'data', '문화축제', '전국 문화축제 데이터.csv')
        # logger.info(f"파일 경로: {file_path}")
        
        if not os.path.exists(file_path):
            logger.error(f"파일이 존재하지 않습니다: {file_path}")
            return []
            
        # 데이터 읽기
        # logger.info("CSV 파일 읽기 시작...")
        df = pd.read_csv(file_path, encoding='utf-8')
        # logger.info(f"전체 데이터 수: {len(df)}")
        
        # 서울 데이터만 필터링
        df = df[df['CTPRVN_NM'] == '서울특별시']
        # logger.info(f"서울 데이터 수: {len(df)}")
        
        all_festivals = []
        for idx, row in df.iterrows():
            try:
                festival = {
                    'festival_name': row['FCLTY_NM'],
                    'area_name': f"서울특별시 {row['RDNMADR_NM']}",
                    'begin_date': row['FSTVL_BEGIN_DE'],
                    'end_date': row['FSTVL_END_DE'],
                    'FCLTY_LA': row['FCLTY_LA'],
                    'FCLTY_LO': row['FCLTY_LO']
                }
                all_festivals.append(festival)
                # logger.info(f"축제 데이터 추가: {festival['festival_name']}")
                
            except Exception as e:
                logger.error(f"행 처리 중 오류 (행 {idx}): {str(e)}")
                continue
                
        # logger.info(f"총 {len(all_festivals)}개의 축제 데이터 처리 완료")
        return all_festivals
        
    except Exception as e:
        logger.error(f"문화축제 데이터 처리 중 오류: {str(e)}", exc_info=True)
        return []

if __name__ == "__main__":
    import_cultural_festivals() 