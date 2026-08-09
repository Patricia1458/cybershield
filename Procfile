release: python manage.py collectstatic --noinput && python manage.py migrate --noinput
web: gunicorn cybershield_project.wsgi --log-file -
