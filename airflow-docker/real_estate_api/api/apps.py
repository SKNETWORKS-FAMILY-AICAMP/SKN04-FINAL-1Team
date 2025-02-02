from django.apps import AppConfig
from django.db import connection


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # 앱이 시작될 때 realestate 스키마 생성
        with connection.cursor() as cursor:
            # 스키마 생성
            cursor.execute("""
                CREATE SCHEMA IF NOT EXISTS realestate;
            """)
            
            # 모든 사용자에게 권한 부여
            cursor.execute("""
                GRANT ALL ON SCHEMA realestate TO PUBLIC;
            """)
            
            # 스키마 검색 경로 설정
            cursor.execute("""
                ALTER DATABASE postgres SET search_path TO realestate, public;
                SET search_path TO realestate, public;
            """)
