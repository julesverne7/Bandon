warning:
	echo "do not run make without parameters"

rebuild_db:
	./manage.py reset_db
	./manage.py makemigrations
	./manage.py migrate


start_worker:
	celery -A backend worker -l INFO

start_beat:
	celery -A backend beat -l INFO
