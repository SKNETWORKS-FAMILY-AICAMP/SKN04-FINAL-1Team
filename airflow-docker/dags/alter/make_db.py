import asyncio
from pathlib import Path
import logging
from .alter import async_engine, Base, check_tables
from .utils import setup_logger

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / 'real_estate.db'
main_logger = setup_logger('alter_main', 'logs/alter_main.log')
error_logger = setup_logger('alter_error', 'logs/alter_error.log', level=logging.ERROR)
db_logger = setup_logger('alter_db', 'logs/alter_db.log')

async def create_tables():
    """테이블 생성"""
    try:
        async with async_engine.begin() as conn:
            # 테이블 존재 여부 확인
            existing_tables = await check_tables(conn)
            
            # 필요한 테이블 목록
            required_tables = ['property_info', 'property_locations', 'sales', 'rentals']
            
            # 누락된 테이블 확인
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:  # 누락된 테이블이 있으면 생성
                main_logger.info(f"누락된 테이블 생성: {missing_tables}")
                await conn.run_sync(Base.metadata.create_all)
                main_logger.info("테이블 생성 완료")
            else:
                main_logger.info(f"모든 테이블이 이미 존재합니다: {existing_tables}")
                
    except Exception as e:
        error_logger.error(f"테이블 생성/확인 중 오류: {str(e)}")
        raise

async def initialize_database():
    """데이터베이스 초기화"""
    try:
        # DB 파일이 없으면 생성
        if not DB_PATH.exists():
            main_logger.info(f"새로운 데이터베이스 생성: {DB_PATH}")
            DB_PATH.touch()

        # 테이블 생성
        await create_tables()

    except Exception as e:
        error_logger.error(f"데이터베이스 초기화 중 오류: {str(e)}")
        raise

def main():
    try:
        # 데이터베이스 초기화
        asyncio.run(initialize_database())
            
    except Exception as e:
        error_logger.error(f"실행 중 오류: {str(e)}")
        return

if __name__ == "__main__":
    main()