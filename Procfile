release: python manage.py makemigrations accounts && python manage.py migrate accounts && python manage.py makemigrations && python manage.py migrate
web: gunicorn spotifyWrapped.wsgi --log-file -