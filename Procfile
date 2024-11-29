release: python manage.py makemigrations accounts && python manage.py migrate accounts
web: gunicorn spotifyWrapped.wsgi --log-file -