FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache \
    postgresql-client

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY ./src /app/src
COPY ./alembic /app/alembic
COPY alembic.ini .

RUN addgroup -S app-group && \
    adduser -S -G app-group app-user && \
    chown -R app-user:app-group /app

USER app-user

ENV PYTHONPATH=/app/src
