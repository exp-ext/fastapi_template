#!/bin/sh

taskiq worker src.conf.taskiq:taskiq_broker --workers=2 --log-level=INFO  --fs-discover
