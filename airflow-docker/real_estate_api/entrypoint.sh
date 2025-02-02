#!/bin/bash

# 데이터베이스 연결 대기
while ! nc -z postgres-data 5432; do
  echo "데이터베이스 서버 대기 중..."
  sleep 1
done

echo "데이터베이스가 준비되었습니다!"

# 마이그레이션 실행
python manage.py migrate
python manage.py runserver 0.0.0.0:8000