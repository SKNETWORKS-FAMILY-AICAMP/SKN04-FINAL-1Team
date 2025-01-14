import pandas as pd
import logging
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.alter_manager.models import CulturalFacility

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '문화시설 데이터를 CSV 파일에서 데이터베이스로 임포트합니다.'

    def handle(self, *args, **options):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        success_count = 0
        fail_count = 0

        try:
            # 1. 기본 문화시설 (나혼자, 실내놀이, 실외놀이)
            facility_files = [
                '나혼자 문화시설 데이터.csv',
                '아이랑 실내 놀이 시설 데이터.csv',
                '아이랑 실외 놀이 시설 데이터.csv'
            ]
            
            for file_name in facility_files:
                try:
                    file_path = os.path.join(settings.BASE_DIR, 'data', '문화시설', file_name)
                    df = pd.read_csv(file_path)
                    # 서울 데이터만 필터링
                    df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
                    
                    for _, row in df.iterrows():
                        try:
                            facility_data = {
                                'name': row['FCLTY_NM'],
                                'facility_type': row['MLSFC_NM'],
                                'district': row['SIGNGU_NM'],
                                'address': row['FCLTY_ROAD_NM_ADDR'],
                                'latitude': float(row['FCLTY_LA']),
                                'longitude': float(row['FCLTY_LO'])
                            }
                            
                            _, created = CulturalFacility.objects.get_or_create(
                                name=facility_data['name'],
                                address=facility_data['address'],
                                defaults=facility_data
                            )
                            
                            if created:
                                success_count += 1
                                self.stdout.write(f"새로운 문화시설 추가됨: {facility_data['name']}")
                            else:
                                CulturalFacility.objects.filter(
                                    name=facility_data['name'],
                                    address=facility_data['address']
                                ).update(**facility_data)
                                success_count += 1
                                self.stdout.write(f"기존 문화시설 업데이트됨: {facility_data['name']}")
                                
                        except Exception as e:
                            logger.error(f"문화시설 데이터 처리 중 오류 ({row['FCLTY_NM']}): {str(e)}")
                            fail_count += 1
                            
                except Exception as e:
                    logger.error(f"파일 처리 중 오류 ({file_name}): {str(e)}")
                    continue

            # 2. 영화관, 전시관
            other_files = [
                '전국 영화관 시설 데이터.csv',
                '전국 전시관 데이터.csv'
            ]
            
            for file_name in other_files:
                try:
                    file_path = os.path.join(settings.BASE_DIR, 'data', '문화시설', file_name)
                    df = pd.read_csv(file_path)
                    # 서울 데이터만 필터링
                    df = df[df['CTPRVN_NM'].str.contains('서울', na=False)]
                    
                    for _, row in df.iterrows():
                        try:
                            # 도로명주소와 건물번호 합치기
                            if pd.isna(row.get('RDNMADR_NM')):
                                # 지번 주소 사용
                                full_address = f"{row['SIGNGU_NM']} {row['LEGALDONG_NM']}"
                                if pd.notna(row.get('LNM_ADDR')):
                                    full_address += f" {row['LNM_ADDR']}"
                            else:
                                full_address = row['RDNMADR_NM']
                                if pd.notna(row.get('BULD_NO')):
                                    full_address = f"{row['RDNMADR_NM']} {row['BULD_NO']}"
                            
                            # 시설명 처리
                            if pd.isna(row.get('POI_NM')):
                                continue
                                
                            facility_name = row['POI_NM']
                            if pd.notna(row.get('BHF_NM')):
                                facility_name = f"{row['POI_NM']} {row['BHF_NM']}"
                            
                            facility_data = {
                                'name': facility_name,
                                'facility_type': row.get('CL_NM', '기타'),
                                'district': row['SIGNGU_NM'],
                                'address': full_address,
                                'latitude': float(row.get('LC_LA', row.get('FCLTY_LA'))),
                                'longitude': float(row.get('LC_LO', row.get('FCLTY_LO')))
                            }
                            
                            _, created = CulturalFacility.objects.get_or_create(
                                name=facility_data['name'],
                                address=facility_data['address'],
                                defaults=facility_data
                            )
                            
                            if created:
                                success_count += 1
                                self.stdout.write(f"새로운 문화시설 추가됨: {facility_data['name']}")
                            else:
                                CulturalFacility.objects.filter(
                                    name=facility_data['name'],
                                    address=facility_data['address']
                                ).update(**facility_data)
                                success_count += 1
                                self.stdout.write(f"기존 문화시설 업데이트됨: {facility_data['name']}")
                                
                        except Exception as e:
                            logger.error(f"문화시설 데이터 처리 중 오류 ({row.get('POI_NM', '알 수 없음')}): {str(e)}")
                            fail_count += 1
                            
                except Exception as e:
                    logger.error(f"파일 처리 중 오류 ({file_name}): {str(e)}")
                    continue

            self.stdout.write(
                self.style.SUCCESS(
                    f'문화시설 데이터 임포트가 완료되었습니다. 성공: {success_count}, 실패: {fail_count}'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'문화시설 데이터 임포트 중 오류가 발생했습니다: {str(e)}')
            ) 