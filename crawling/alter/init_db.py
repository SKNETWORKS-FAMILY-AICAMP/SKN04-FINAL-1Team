import os
from sqlalchemy import create_engine, inspect
from models import Base
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """데이터베이스 초기화 및 테이블 생성"""
    try:
        # 현재 디렉토리 확인
        current_dir = os.getcwd()
        db_path = os.path.join(current_dir, 'real_estate.db')
        logger.info(f"현재 디렉토리: {current_dir}")
        logger.info(f"데이터베이스 경로: {db_path}")

        # SQLite 데이터베이스 연결
        engine = create_engine(
            f'sqlite:///{db_path}',
            echo=True,  # SQL 로깅 활성화
            connect_args={
                'timeout': 30,
                'check_same_thread': False
            }
        )
        
        # Base에 정의된 모든 테이블 확인
        logger.info("정의된 테이블 목록:")
        for table in Base.metadata.tables.keys():
            logger.info(f"- {table}")
        
        # 모든 테이블 생성
        logger.info("테이블 생성 시작...")
        Base.metadata.create_all(engine)
        
        # 생성된 테이블 확인
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info("생성된 테이블 목록:")
        for table in created_tables:
            logger.info(f"- {table}")
            
        if not created_tables:
            logger.error("테이블이 생성되지 않았습니다!")
        else:
            logger.info("데이터베이스 테이블이 성공적으로 생성되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}", exc_info=True)
        raise e

if __name__ == "__main__":
    init_database()