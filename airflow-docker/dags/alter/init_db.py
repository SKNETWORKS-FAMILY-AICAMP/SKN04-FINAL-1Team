from alter.models import Base
from alter.db_config import engine

def init_database():
    """데이터베이스 초기화"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_database()