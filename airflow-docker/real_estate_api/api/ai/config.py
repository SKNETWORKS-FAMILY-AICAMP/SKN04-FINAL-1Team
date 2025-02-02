"""
프로젝트 환경설정 파일.

.env 파일을 사용하여 PostgreSQL 데이터베이스 설정을 불러온다.
"""

import os  # OS 환경 변수 로드
from dotenv import load_dotenv  # .env 파일 로드

__all__ = ['config', 'DB_CONFIG']

# ✅ .env 파일 로드
load_dotenv()

# ✅ PostgreSQL 접속 정보
DB_CONFIG = {
    "user": os.getenv("DB_USER", "realestate"),       
    "password": os.getenv("DB_PASSWORD", "realestate"),
    "host": os.getenv("DB_HOST", "postgres-data"),    
    "port": os.getenv("DB_PORT", "5432"),          
    "database": os.getenv("DB_NAME", "realestate") 
}

# ✅ OpenAI API 설정
config = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "model_name": "gpt-4-turbo-preview",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
}
