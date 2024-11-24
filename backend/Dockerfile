FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache \
    postgresql-client \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt  --no-cache-dir && \
    pip install psycopg2  --no-cache-dir

COPY . .

ENV PYTHONPATH=/app

RUN addgroup -S app-group && \
    adduser -S -G app-group app-user && \
    chown -R app-user:app-group /app

USER app-user