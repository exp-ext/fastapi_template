#!/bin/sh

celery -A src.conf.celery_app worker -l info -P threads --concurrency=1 --max-tasks-per-child=100
