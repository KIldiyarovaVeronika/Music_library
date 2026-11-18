#!/bin/sh
set -e

echo "Waiting for postgres..."
python - <<'PY'
import os, time, psycopg2
while True:
    try:
        psycopg2.connect(
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ.get("POSTGRES_HOST", "db"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
        ).close()
        break
    except psycopg2.OperationalError:
        time.sleep(1)
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "$DJANGO_DEBUG" = "True" ]; then
    exec python manage.py runserver 0.0.0.0:8000
else
    exec gunicorn myproject.wsgi:application --bind 0.0.0.0:8000
fi