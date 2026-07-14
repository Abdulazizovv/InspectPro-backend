#!/usr/bin/env bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting ASGI server..."
exec gunicorn -k uvicorn.workers.UvicornWorker core.asgi:application \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --access-logformat '{"ts":"%(t)s","remote_addr":"%(h)s","request_id":"%({X-Request-ID}i)s","method":"%(m)s","path":"%(U)s","query":"%(q)s","status":%(s)s,"bytes":%(B)s,"referrer":"%(f)s","ua":"%(a)s","request_time":%(L)s}'
