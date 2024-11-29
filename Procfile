release: python manage.py makemigrations && python manage.py migrate
web: gunicorn spotifyWrapped.wsgi --log-file -