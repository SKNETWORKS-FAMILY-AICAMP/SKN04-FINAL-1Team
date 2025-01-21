from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from alter.import_subway_stations import import_subway_stations
from alter.import_cultural_facilities import import_cultural_facilities
from alter.import_cultural_festivals import import_cultural_festivals
from alter.import_crime_stats import import_crime_stats
from alter.import_real_estate import run_import_real_estate
from alter.calculate_distances import calculate_distances
from alter.update_address_coordinates import update_address_coordinates, update_missing_property_coordinates

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['jeonhun6084@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 매일 실행되는 DAG (부동산 매물)
with DAG(
    'import_real_estate_daily',
    default_args=default_args,
    description='부동산 매물 데이터 수집',
    schedule_interval='0 0 * * *',
    start_date=pendulum.datetime(2024, 1, 1, tz='Asia/Seoul'),
    catchup=False,
) as dag_daily:
    import_real_estate_data = PythonOperator(
        task_id='import_real_estate_data',
        python_callable=run_import_real_estate,
    )
    
    calculate_distances_task = PythonOperator(
        task_id='calculate_distances',
        python_callable=calculate_distances,
    )
    
    # 작업 순서 설정
    import_real_estate_data >> calculate_distances_task

# 매일 새벽 2시에 실행되는 DAG (주소 좌표 업데이트)
with DAG(
    'update_address_coordinates_daily',
    default_args=default_args,
    description='Update coordinates for addresses and properties daily',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2025, 1, 1),
    catchup=False
) as dag_address:
    # 1. 주소 좌표 업데이트 태스크
    t1 = PythonOperator(
        task_id='update_address_coordinates',
        python_callable=update_address_coordinates,
        dag=dag_address,
    )

    # 2. 매물 좌표 업데이트 태스크
    t2 = PythonOperator(
        task_id='update_property_coordinates',
        python_callable=update_missing_property_coordinates,
        dag=dag_address,
    )

    # 태스크 순서 설정
    t1 >> t2

# 수동 실행 DAG (거리 계산)
with DAG(
    'calculate_distances_manual',
    default_args=default_args,
    description='거리 계산 수동 실행',
    schedule_interval=None,  # 수동 실행
    start_date=pendulum.datetime(2024, 1, 1, tz='Asia/Seoul'),
    catchup=False,
) as dag_distances_manual:
    calculate_distances_manual = PythonOperator(
        task_id='calculate_distances_manual',
        python_callable=calculate_distances,
    )

# 분기별 실행되는 DAG (범죄 통계)
with DAG(
    'import_crime_stats_quarterly',
    default_args=default_args,
    description='범죄 통계 데이터 수집',
    schedule_interval='0 0 1 */3 *',
    start_date=pendulum.datetime(2024, 1, 1, tz='Asia/Seoul'),
    catchup=False,
) as dag_quarterly:
    import_crime_stats_data = PythonOperator(
        task_id='import_crime_stats_data',
        python_callable=import_crime_stats,
    )

# 연간 실행되는 DAG (문화시설, 축제)
with DAG(
    'import_cultural_yearly',
    default_args=default_args,
    description='문화시설 및 축제 데이터 수집',
    schedule_interval='0 0 1 1 *',
    start_date=pendulum.datetime(2024, 1, 1, tz='Asia/Seoul'),
    catchup=False,
) as dag_yearly:
    import_cultural_facilities_data = PythonOperator(
        task_id='import_cultural_facilities_data',
        python_callable=import_cultural_facilities,
    )

    import_cultural_festivals_data = PythonOperator(
        task_id='import_cultural_festivals_data',
        python_callable=import_cultural_festivals,
    )

# 수동 실행 DAG (지하철)
with DAG(
    'import_subway_manual',
    default_args=default_args,
    description='지하철역 데이터 수집',
    schedule_interval=None,
    start_date=pendulum.datetime(2024, 1, 1, tz='Asia/Seoul'),
    catchup=False,
) as dag_manual:
    import_subway_data = PythonOperator(
        task_id='import_subway_data',
        python_callable=import_subway_stations,
    ) 