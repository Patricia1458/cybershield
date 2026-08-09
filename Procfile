release: python manage.py collectstatic --noinput && python manage.py migrate --noinput
web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && gunicorn cybershield_project.wsgi --log-file -
