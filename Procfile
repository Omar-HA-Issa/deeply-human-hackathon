web: sh -c "python manage.py migrate --verbosity 2 && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT"
