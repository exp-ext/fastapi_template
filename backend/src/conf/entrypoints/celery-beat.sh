#!/bin/sh

POSTGRES_HOST="db"
POSTGRES_DB="celery_schedule_jobs"

DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_PORT=${POSTGRES_PORT:-5432}

# Проверка, существует ли база данных
psql -U $DB_USER -h $POSTGRES_HOST -p $DB_PORT -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1

# Если база данных не существует, создаём её
if [ $? -eq 1 ]; then
    echo "База данных $POSTGRES_DB не существует. Создаём..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -h $POSTGRES_HOST -p $DB_PORT -d postgres -c "CREATE DATABASE $POSTGRES_DB"
else
    echo "База данных $POSTGRES_DB уже существует."
fi

# Запускаем Celery
celery -A src.conf.celery_app beat -l info