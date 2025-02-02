#!/bin/bash

# 데이터베이스 연결 대기
echo "데이터베이스 연결 대기 중..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "데이터베이스 연결 완료"

# 마이그레이션 실행
echo "마이그레이션 실행 중..."
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate admin
python manage.py migrate sessions
python manage.py makemigrations
python manage.py migrate api
python manage.py migrate

# static 파일 수집
echo "Static 파일 수집 중..."
mkdir -p staticfiles
python manage.py collectstatic --noinput --clear

# 서버 시작
echo "Gunicorn 서버 시작"
gunicorn real_estate_api.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class gunicorn.workers.sync.SyncWorker \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --reload 