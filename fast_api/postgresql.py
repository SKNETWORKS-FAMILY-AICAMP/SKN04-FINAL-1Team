"""
PostgreSQL 데이터베이스 관리 모듈.

SQLAlchemy를 사용하여 PostgreSQL과 연결하고,
LangChain을 활용한 SQLDatabase 객체를 제공한다.
"""

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from langchain_community.utilities import SQLDatabase
from config import DB_CONFIG  # 🔹 설정 로드, 추후 연결시 여기서 수정


def create_postgresql_engine():
    """
    PostgreSQL 데이터베이스 연결 엔진을 생성하는 함수.

    Returns:
        sqlalchemy.engine.Engine: 데이터베이스 연결 엔진 객체
        None: 연결 실패 시 None 반환
    """
    try:
        engine = create_engine(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}",
            poolclass=NullPool  # 🔹 커넥션 풀링 비활성화 (단일 연결 사용)
        )
        print("✅ PostgreSQL 데이터베이스 연결 성공!")
        return engine
    except Exception as e:
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
    if engine:
        db = SQLDatabase(engine, sample_rows_in_table_info=False)
        print(f"✅ LangChain SQLDatabase 객체 생성 완료!")
        return db
    print("❌ PostgreSQL 연결 실패로 SQLDatabase 객체를 생성하지 못했습니다.")
    return None


# ✅ LangChain SQLDatabase 객체 생성
db = create_sql_database()
