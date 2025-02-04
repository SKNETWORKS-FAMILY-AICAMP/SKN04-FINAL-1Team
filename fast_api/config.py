"""
프로젝트 환경설정 파일.

.env 파일을 사용하여 PostgreSQL 데이터베이스 설정을 불러온다.
"""

import os  # OS 환경 변수 로드
from dotenv import load_dotenv  # .env 파일 로드

# ✅ .env 파일 로드
load_dotenv()

# ✅ PostgreSQL 접속 정보
DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "realestate"),       # 기본값: "postgres"
    "password": os.getenv("POSTGRES_PASSWORD", "realestate"),   # 기본값: "1234"
    "host": os.getenv("POSTGRES_HOST", "airflow-docker-postgres-data-1"),      # 기본값: "localhost"
    "port": os.getenv("POSTGRES_PORT", "5432"),           # 기본값: "5432"
    "database": os.getenv("POSTGRES_DB", "realestate") # 기본값: "real_estate"
}

