from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import pendulum
from alter.import_subway_stations import import_subway_stations
from alter.import_cultural_facilities import import_cultural_facilities
from alter.import_cultural_festivals import import_cultural_festivals
from alter.import_crime_stats import import_crime_stats
from alter.import_real_estate import run_import_real_estate

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['jeonhun6084@gmail.com'],
    'email_on_failure': True,
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
        dag=dag_daily,
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