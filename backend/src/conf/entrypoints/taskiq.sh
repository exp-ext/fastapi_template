#!/bin/sh

taskiq worker src.conf.taskiq:taskiq_app --workers=1 --log-level=INFO
