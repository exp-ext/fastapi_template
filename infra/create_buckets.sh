#!/bin/sh

# Список бакетов
BUCKETS=()
while IFS='=' read -r name value; do
    if [ "${name#*_BUCKET}" != "$name" ]; then
        BUCKETS+=("$value")
    fi
done < <(printenv)

# Ожидание запуска MinIO
while ! curl -s http://localhost:9000/minio/health/live; do
    sleep 1
done

# Установка алиаса для MinIO
mc alias set myminio http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD}

# Создание бакетов и установка анонимных политик доступа
for BUCKET in "${BUCKETS[@]}"; do
    if ! mc ls myminio/${BUCKET} > /dev/null 2>&1; then
        mc mb myminio/${BUCKET}
        mc anonymous set public myminio/${BUCKET}
        echo "Bucket ${BUCKET} created."
    else
        echo "Bucket ${BUCKET} already exists."
    fi
done
