import pandas as pd
import logging
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.alter_manager.models import CrimeRate

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '범죄율 데이터를 CSV 파일에서 데이터베이스로 임포트합니다.'

    # 주요 범죄 유형 정의
    STARRED_CRIMES = [
        '살인기수', '살인미수등', '강도', '강간', '유사강간',
        '강제추행', '기타 강간 강제추행등', '상해', '폭행', '협박', 
        '폭력행위등', '손괴', '사기'
    ]

    # 구청 코드와 구 이름 매핑
    DISTRICT_CODE_TO_NAME = {
        '11680': '강남구', '11740': '강동구', '11305': '강북구',
        '11500': '강서구', '11620': '관악구', '11215': '광진구',
        '11530': '구로구', '11545': '금천구', '11350': '노원구',
        '11320': '도봉구', '11230': '동대문구', '11590': '동작구',
        '11440': '마포구', '11410': '서대문구', '11650': '서초구',
        '11200': '성동구', '11290': '성북구', '11710': '송파구',
        '11470': '양천구', '11560': '영등포구', '11170': '용산구',
        '11380': '은평구', '11110': '종로구', '11140': '중구',
        '11260': '중랑구'
    }

    def get_all_district_populations(self):
        """서울시 전체 구의 인구 데이터를 한 번에 가져옵니다."""
        api_key = "7169716b6c786f643731576f535869"
        url = f"http://openapi.seoul.go.kr:8088/{api_key}/xml/SPOP_LOCAL_RESD_JACHI/1/25/"
        
        population_data = {}
        try:
            response = requests.get(url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                result_code = root.find('.//CODE')
                if result_code is not None and result_code.text != 'INFO-000':
                    self.stdout.write(self.style.ERROR(f"API 오류: {root.find('.//MESSAGE').text}"))
                    return population_data
                
                for row in root.findall('.//row'):
                    district_code = row.find('ADSTRD_CODE_SE').text[:5]
                    population = float(row.find('TOT_LVPOP_CO').text)
                    population_data[district_code] = population
                    
                self.stdout.write(f"인구 데이터 가져오기 성공: {len(population_data)}개 구")
            else:
                self.stdout.write(self.style.ERROR(f"API 호출 실패 (상태 코드: {response.status_code})"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"인구 데이터 API 호출 중 오류: {str(e)}"))
        
        return population_data

    def process_crime_data(self, df, district_col, district_name, population):
        """각 구의 범죄 데이터를 처리합니다."""
        crime_details = []
        total_crime_count = 0

        # 주요 범죄 유형별 통계 수집
        for crime_type in self.STARRED_CRIMES:
            crime_rows = df[df['범죄중분류'] == crime_type]
            if not crime_rows.empty:
                crime_count = int(crime_rows[district_col].iloc[0])
                total_crime_count += crime_count
                crime_category = crime_rows['범죄대분류'].iloc[0]
                
                crime_details.append({
                    'category': crime_category,
                    'subcategory': crime_type,
                    'count': crime_count
                })

        return total_crime_count, crime_details

    def handle(self, *args, **options):
        try:
            # 전체 구의 인구 데이터를 한 번에 가져옴
            district_populations = self.get_all_district_populations()
            if not district_populations:
                self.stdout.write(self.style.ERROR("인구 데이터를 가져오는데 실패했습니다."))
                return

            # CSV 파일 읽기
            file_path = os.path.join(settings.BASE_DIR, 'data', '범죄율', '서울시_범죄_통계.csv')
            df = pd.read_csv(file_path, encoding='utf-8')
            
            success_count = 0
            fail_count = 0
            
            # 구 목록 추출
            district_columns = [col for col in df.columns if '서울' in col]
            
            # 각 구별로 처리
            for district_col in district_columns:
                district_name = district_col.replace('서울', '').strip()
                self.stdout.write(f"\n처리 중인 구: {district_name}")
                
                try:
                    # 구청 코드 찾기
                    district_code = next((code for code, name in self.DISTRICT_CODE_TO_NAME.items() 
                                       if name == district_name), None)
                    if not district_code:
                        self.stdout.write(self.style.WARNING(f"구청 코드를 찾을 수 없음: {district_name}"))
                        continue

                    # 인구수 확인
                    population = district_populations.get(district_code)
                    if population is None:
                        self.stdout.write(self.style.WARNING(f"{district_name} 인구 데이터를 찾을 수 없습니다."))
                        continue

                    # 범죄 데이터 처리
                    total_crime_count, crime_details = self.process_crime_data(df, district_col, district_name, population)
                    
                    # 범죄율 계산 (10만명당)
                    crime_rate = (total_crime_count / population) * 100000
                    
                    # DB에 저장 또는 업데이트
                    crime_data = {
                        'district': district_name,
                        'year': datetime.now().year,
                        'crime_count': total_crime_count,
                        'population': int(population),
                        'rate': float(crime_rate)
                    }
                    
                    crime_obj, created = CrimeRate.objects.update_or_create(
                        district=district_name,
                        year=datetime.now().year,
                        defaults=crime_data
                    )
                    
                    # 범죄 상세 정보 출력
                    self.stdout.write(f"\n{district_name} 범죄 통계:")
                    for detail in crime_details:
                        self.stdout.write(f"- {detail['subcategory']}: {detail['count']:,}건")
                    
                    success_count += 1
                    status = "생성됨" if created else "업데이트됨"
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n{district_name} 데이터 {status}:"
                            f"\n- 총 범죄 건수: {total_crime_count:,}"
                            f"\n- 인구수: {int(population):,}"
                            f"\n- 범죄율(10만명당): {crime_rate:.2f}"
                        )
                    )
                    
                except Exception as e:
                    fail_count += 1
                    self.stdout.write(self.style.ERROR(f"\n{district_name} 처리 중 오류 발생: {str(e)}"))
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n범죄율 데이터 임포트가 완료되었습니다.'
                    f'\n- 성공: {success_count}개 구'
                    f'\n- 실패: {fail_count}개 구'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'범죄율 데이터 임포트 중 오류가 발생했습니다: {str(e)}')
            )