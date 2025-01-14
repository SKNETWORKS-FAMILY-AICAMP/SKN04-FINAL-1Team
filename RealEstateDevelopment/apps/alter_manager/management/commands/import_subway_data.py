import pandas as pd
import logging
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.alter_manager.models import SubwayStation

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '지하철역 데이터를 CSV 파일에서 데이터베이스로 임포트합니다.'

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        try:
            file_path = os.path.join(settings.BASE_DIR, 'data', '지하철', 'seoul_subway_stations.csv')
            df = pd.read_csv(file_path)
            
            success_count = 0
            fail_count = 0
            
            for _, row in df.iterrows():
                try:
                    station_data = {
                        'station_id': str(row['역ID']),
                        'station_name': str(row['역이름']),
                        'description': str(row['설명']) if pd.notna(row['설명']) else '',
                        'latitude': float(row['위도']),
                        'longitude': float(row['경도'])
                    }
                    
                    _, created = SubwayStation.objects.get_or_create(
                        station_id=station_data['station_id'],
                        defaults=station_data
                    )
                    
                    if created:
                        success_count += 1
                        self.stdout.write(f"새로운 역 추가됨: {station_data['station_name']}")
                    else:
                        # 기존 데이터 업데이트
                        SubwayStation.objects.filter(station_id=station_data['station_id']).update(**station_data)
                        success_count += 1
                        self.stdout.write(f"기존 역 업데이트됨: {station_data['station_name']}")
                        
                except Exception as e:
                    logger.error(f"역 데이터 처리 중 오류 ({row['역이름']}): {str(e)}")
                    fail_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'지하철역 데이터 임포트가 완료되었습니다. 성공: {success_count}, 실패: {fail_count}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'지하철역 데이터 임포트 중 오류가 발생했습니다: {str(e)}')
            ) 