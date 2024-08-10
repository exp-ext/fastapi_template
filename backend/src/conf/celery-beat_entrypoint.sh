#!/bin/sh

celery -A src.conf.celery_app beat -l info
