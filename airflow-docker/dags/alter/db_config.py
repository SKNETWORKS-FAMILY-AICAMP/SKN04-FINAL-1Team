import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from functools import wraps
from airflow.models import Variable

load_dotenv()

# 데이터 DB 연결 정보 - docker-compose.yaml의 postgres-data 서비스 설정과 일치
DATA_DB_USER = Variable.get("DATA_DB_USER")
DATA_DB_PASSWORD = Variable.get("DATA_DB_PASSWORD")
DATA_DB_HOST = Variable.get("DATA_DB_HOST")
DATA_DB_PORT = Variable.get("DATA_DB_PORT")
DATA_DB_NAME = Variable.get("DATA_DB_NAME")

# 데이터 DB 연결 URL
DATA_DB_URL = f'postgresql://{DATA_DB_USER}:{DATA_DB_PASSWORD}@{DATA_DB_HOST}:{DATA_DB_PORT}/{DATA_DB_NAME}'

# 엔진 생성
engine = create_engine(
    DATA_DB_URL,
    connect_args={'options': '-c search_path=realestate,public'}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    return SessionLocal()

def provide_session(func):
    """세션을 제공하는 데코레이터"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_session()
        try:
            kwargs['session'] = session
            result = func(*args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()
    return wrapper

@contextmanager
def session_scope():
    """세션 컨텍스트 매니저"""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()