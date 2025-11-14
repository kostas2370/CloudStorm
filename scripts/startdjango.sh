#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

python manage.py migrate
python manage.py loaddata fixtures/fixtures.json || true
python manage.py collectstatic --noinput

if [ "${DJANGO_ENV:-production}" = "development" ]; then
    echo "Starting development server"
    python manage.py runserver 0.0.0.0:8000
else
    echo "Starting production server"
    gunicorn CloudStorm.wsgi:application --bind 0.0.0.0:8000
fi