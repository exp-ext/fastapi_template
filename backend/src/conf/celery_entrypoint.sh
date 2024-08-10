#!/bin/sh

celery -A src.conf.celery_app worker -l info -P gevent
