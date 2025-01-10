from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import pendulum
import sys
import os

# alter 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alter import alter
from alter.import_all_data import import_all_data
from alter.import_subway_stations import import_subway_stations
from alter.import_cultural_facilities import import_cultural_facilities
from alter.import_cultural_festivals import import_cultural_festivals
from alter.import_crime_stats import import_crime_stats
from alter.import_population_stats import import_population_stats

# 공통 default_args
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    
    # 이메일 알림 설정
    'email': ['your-email@example.com'],
    'email_on_failure': True,
    'email_on_retry': True,
    'email_on_success': False,
    
    # 재시도 설정
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
    
    # 타임아웃 설정
    'execution_timeout': timedelta(hours=2),
    'dagrun_timeout': timedelta(hours=4),
    
    # 시작 시간 설정 (한국 시간)
    'start_date': pendulum.datetime(2024, 3, 1, tz='Asia/Seoul'),
}

# 매물 데이터 수집 DAG (매일)
property_dag = DAG(
    'property_data_pipeline',
    default_args=default_args,
    description='부동산 매물 데이터 수집 파이프라인',
    
    # 스케줄링 설정
    schedule_interval='0 1 * * *',
    catchup=False,  # 과거 실행 건너뛰기
    
    # 동시성 설정
    max_active_runs=1,  # 동시에 실행될 수 있는 DAG 인스턴스 수
    concurrency=2,  # 동시에 실행될 수 있는 태스크 수
    
    # 태그 설정 (Airflow UI에서 필터링 용이)
    tags=['real_estate', 'property', 'daily'],
    
    # 문서화
    doc_md="""
    ## 부동산 매물 데이터 수집 파이프라인
    
    매일 새벽 1시에 실행되며 다음 작업을 수행합니다:
    - 부동산 매물 데이터 수집
    - DB 저장
    
    ### 연락처
    - 담당자: 김정훈
    - 이메일: jeonhun6084@gmail.com
    """,
)

def run_property_crawler():
    """부동산 매물 데이터 수집"""
    alter.main()

crawl_properties = PythonOperator(
    task_id='crawl_properties',
    python_callable=run_property_crawler,
    
    # 타임아웃 설정
    execution_timeout=timedelta(hours=2),
    
    # 재시도 규칙
    retries=3,
    retry_delay=timedelta(minutes=5),
    retry_exponential_backoff=True,
    
    # 트리거 규칙
    trigger_rule=TriggerRule.ALL_SUCCESS,  # 기본값
    
    # 태스크 우선순위
    priority_weight=10,
    
    # 에러 처리를 위한 콜백 함수
    on_failure_callback=lambda context: handle_failure(context),
    on_success_callback=lambda context: handle_success(context),
    on_retry_callback=lambda context: handle_retry(context),
    
    # 환경 변수 설정
    env={'PYTHONPATH': os.environ.get('PYTHONPATH', '')},
    
    dag=property_dag,
)

# 콜백 함수 예시
def handle_failure(context):
    """태스크 실패 시 처리"""
    task_instance = context['task_instance']
    print(f"Task {task_instance.task_id} failed in DAG {task_instance.dag_id}")

def handle_success(context):
    """태스크 성공 시 처리"""
    pass

def handle_retry(context):
    """태스크 재시도 시 처리"""
    pass

# 보조 데이터 수집 DAG (월 1회)
auxiliary_dag = DAG(
    'auxiliary_data_pipeline',
    default_args=default_args,
    description='보조 데이터(지하철, 문화시설 등) 수집 파이프라인',
    schedule_interval='0 0 1 * *',  # 매월 1일 자정
    catchup=False,
    max_active_runs=1,
    tags=['real_estate', 'auxiliary', 'monthly'],
    doc_md="""
    ## 보조 데이터 수집 파이프라인
    
    매월 1일 자정에 실행되며 다음 작업을 수행합니다:
    1. 지하철역 데이터 수집
    2. 문화시설 데이터 수집
    3. 문화축제 데이터 수집
    4. 범죄통계 데이터 수집
    5. 인구통계 데이터 수집
    
    ### 연락처
    - 담당자: 김정훈
    - 이메일: jeonhun6084@gmail.com
    """,
)

# 지하철역 데이터 수집
subway_task = PythonOperator(
    task_id='import_subway_stations',
    python_callable=lambda: import_subway_stations(None),  # session은 함수 내에서 생성
    execution_timeout=timedelta(minutes=10),
    retry_delay=timedelta(minutes=2),
    retries=2,
    dag=auxiliary_dag,
)

# 문화시설 데이터 수집
facilities_task = PythonOperator(
    task_id='import_cultural_facilities',
    python_callable=lambda: import_cultural_facilities(None),
    execution_timeout=timedelta(minutes=10),
    retry_delay=timedelta(minutes=2),
    retries=2,
    dag=auxiliary_dag,
)

# 문화축제 데이터 수집
festivals_task = PythonOperator(
    task_id='import_cultural_festivals',
    python_callable=lambda: import_cultural_festivals(None),
    execution_timeout=timedelta(minutes=10),
    retry_delay=timedelta(minutes=2),
    retries=2,
    dag=auxiliary_dag,
)

# 범죄통계 데이터 수집
crime_task = PythonOperator(
    task_id='import_crime_stats',
    python_callable=lambda: import_crime_stats(None),
    execution_timeout=timedelta(minutes=10),
    retry_delay=timedelta(minutes=2),
    retries=2,
    dag=auxiliary_dag,
)

# 인구통계 데이터 수집
population_task = PythonOperator(
    task_id='import_population_stats',
    python_callable=lambda: import_population_stats(None),
    execution_timeout=timedelta(minutes=10),
    retry_delay=timedelta(minutes=2),
    retries=2,
    dag=auxiliary_dag,
)

# 태스크 순서 설정 (병렬 실행)
[subway_task, facilities_task, festivals_task, crime_task, population_task]

# 매물 데이터 수집 태스크는 그대로 유지
crawl_properties 