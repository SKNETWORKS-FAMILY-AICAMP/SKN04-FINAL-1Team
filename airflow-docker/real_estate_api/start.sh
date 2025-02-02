#!/bin/sh
cd /app
python manage.py migrate
python manage.py collectstatic --noinput
exec gunicorn real_estate_api.wsgi:application --bind 0.0.0.0:8000 