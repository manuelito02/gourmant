#!/bin/sh
set -e
pybabel compile -d translations -f
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
