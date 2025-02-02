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


# 서버 시작
echo "Django 서버 시작"
python manage.py runserver 0.0.0.0:8000 