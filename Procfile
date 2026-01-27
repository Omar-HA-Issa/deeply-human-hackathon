web: python manage.py migrate && python manage.py collectstatic --noinput && python manage.py load_countries && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT
