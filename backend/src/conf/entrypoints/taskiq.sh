#!/bin/sh
taskiq worker src.conf.taskiq:taskiq_broker --workers=4 --log-level=INFO  --fs-discover &
taskiq scheduler src.conf.taskiq:scheduler --log-level=INFO
