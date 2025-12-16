#!/bin/bash

echo "Приминение миграций..."
python manage.py migrate

echo "Сбор статики..."
python manage.py collectstatic --noinput
cp -r /app/collected_static/. /backend_static/static/

echo "Запуск gunicorn..."
gunicorn --bind 0.0.0.0:8000 foodgram_st_backend.wsgi