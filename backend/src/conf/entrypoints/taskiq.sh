#!/bin/sh
TASKIQ_PROCESS=1 taskiq worker src.conf.taskiq:taskiq_broker --workers=4 --log-level=INFO  --fs-discover &
TASKIQ_PROCESS=1 taskiq scheduler src.conf.taskiq:scheduler --log-level=INFO
