#!/bin/bash

HOSTS_FILE="/etc/hosts"
ENTRIES=(
    "127.0.0.1 www.localhost"
    "127.0.0.1 aws.localhost"
    "127.0.0.1 console.localhost"
)

# Проверка и добавление каждой записи
for ENTRY in "${ENTRIES[@]}"; do
    if grep -qF "$ENTRY" "$HOSTS_FILE"; then
        echo "Запись '$ENTRY' уже существует в файле hosts."
    else
        echo "$ENTRY" | sudo tee -a "$HOSTS_FILE" > /dev/null
        echo "Запись '$ENTRY' успешно добавлена в файл hosts."
    fi
done
