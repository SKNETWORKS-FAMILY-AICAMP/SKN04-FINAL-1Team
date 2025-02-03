"""
PostgreSQL 데이터베이스 관리 모듈.

SQLAlchemy를 사용하여 PostgreSQL과 연결하고,
LangChain을 활용한 SQLDatabase 객체를 제공한다.
"""

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool
from langchain_community.utilities import SQLDatabase
from config import DB_CONFIG  # 🔹 설정 로드, 추후 연결시 여기서 수정
from sqlalchemy import text


def create_postgresql_engine():
    """
    PostgreSQL 데이터베이스 연결 엔진을 생성하는 함수.

    Returns:
        sqlalchemy.engine.Engine: 데이터베이스 연결 엔진 객체
        None: 연결 실패 시 None 반환
    """
    try:
        DATABASE_URL = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        print(f"🔹 DATABASE_URL: {DATABASE_URL}")  # 추가해서 값 확인!

        engine = create_engine(DATABASE_URL, poolclass=NullPool)  # ✅ 연결 풀링 비활성화
        print("✅ PostgreSQL 데이터베이스 연결 성공!")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ DB 연결 테스트 성공! 결과: {result.fetchall()}")
            
        return engine
    except SQLAlchemyError as e:
        print(f"❌ 데이터베이스 연결 중 오류 발생: {str(e)}")
        return None
    
# ✅ PostgreSQL 엔진 생성
engine = create_postgresql_engine()


def create_sql_database():
    """
    LangChain SQLDatabase 객체를 생성하는 함수.

    Returns:
        SQLDatabase 객체 또는 None
    """
    if not engine:
        print("❌ PostgreSQL 연결 실패로 SQLDatabase 객체를 생성하지 못했습니다.")
        return None

    try:
        db = SQLDatabase(engine, schema="realestate", sample_rows_in_table_info=False)
        print("✅ LangChain SQLDatabase 객체 생성 완료!")
        return db

    except Exception as e:
        print("❌ SQLDatabase 객체 생성 실패")
        print(f"🔹 상세 에러 메시지: {e}")
        import traceback
        traceback.print_exc()  # 🛠 에러 상세 로그 출력



# ✅ LangChain SQLDatabase 객체 생성
db = create_sql_database()
