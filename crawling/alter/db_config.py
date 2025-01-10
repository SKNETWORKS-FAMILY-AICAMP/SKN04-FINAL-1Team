from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 데이터베이스 파일 경로 설정
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'real_estate.db'))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# 동기 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()