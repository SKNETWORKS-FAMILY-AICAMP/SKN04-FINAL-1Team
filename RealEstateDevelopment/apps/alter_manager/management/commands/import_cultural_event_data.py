import os
import pandas as pd
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.alter_manager.models import CulturalEvent
from django.db import transaction
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '문화축제 데이터를 데이터베이스로 가져옵니다.'

    def parse_date(self, date_str):
        """날짜 문자열을 파싱하여 날짜 객체로 변환"""
        try:
            # 다양한 날짜 형식 처리
            date_formats = ['%Y%m%d', '%Y-%m-%d']
            
            for date_format in date_formats:
                try:
                    return datetime.strptime(str(date_str).strip(), date_format).date()
                except ValueError:
                    continue
                    
            raise ValueError(f"지원하지 않는 날짜 형식: {date_str}")
            
        except (ValueError, TypeError) as e:
            self.stderr.write(
                self.style.WARNING(f"날짜 변환 오류: {str(e)}")
            )
            return None

    def handle(self, *args, **options):
        try:
            # 파일 경로 설정
            file_path = os.path.join(settings.BASE_DIR, 'data', '문화축제', '전국 문화축제 데이터.csv')
            
            if not os.path.exists(file_path):
                self.stderr.write(self.style.ERROR(f'파일이 존재하지 않습니다: {file_path}'))
                return
                
            # 데이터 읽기
            self.stdout.write(self.style.SUCCESS('CSV 파일 읽기 시작...'))
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # 서울 데이터만 필터링
            df = df[df['CTPRVN_NM'] == '서울특별시']
            self.stdout.write(self.style.SUCCESS(f'서울 데이터 수: {len(df)}'))
            
            success_count = 0
            update_count = 0
            error_count = 0
            
            with transaction.atomic():
                for idx, row in df.iterrows():
                    try:
                        if pd.isna(row['RDNMADR_NM']) or pd.isna(row['FCLTY_NM']):
                            continue
                            
                        district = row['RDNMADR_NM'].split()[0]
                        name = row['FCLTY_NM'].strip()
                        
                        # 날짜 파싱
                        start_date = self.parse_date(row['FSTVL_BEGIN_DE'])
                        end_date = self.parse_date(row['FSTVL_END_DE'])
                        
                        if not start_date or not end_date:
                            self.stderr.write(
                                self.style.WARNING(f'날짜 형식 오류 (행 {idx}): {row["FSTVL_BEGIN_DE"]} - {row["FSTVL_END_DE"]}')
                            )
                            error_count += 1
                            continue
                        
                        # 기존 데이터 확인
                        event, created = CulturalEvent.objects.update_or_create(
                            name=name,
                            district=district,
                            defaults={
                                'start_date': start_date,
                                'end_date': end_date,
                                'description': f"서울특별시 {row['RDNMADR_NM']}"
                            }
                        )
                        
                        if created:
                            success_count += 1
                        else:
                            update_count += 1
                            
                    except Exception as e:
                        self.stderr.write(
                            self.style.ERROR(f'행 처리 중 오류 (행 {idx}): {str(e)}')
                        )
                        error_count += 1
                        continue
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'문화축제 데이터 처리 완료 (신규: {success_count}개, 업데이트: {update_count}개, 오류: {error_count}개)'
                )
            )
            
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f'문화축제 데이터 처리 중 오류: {str(e)}')
            ) 