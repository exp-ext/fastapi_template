#!/bin/sh

alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8100
