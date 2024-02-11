
install:
	poetry install

dev:
	poetry run flask --debug --app page_analyzer:app run

TCP_PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(TCP_PORT) page_analyzer:app

lint:
	poetry run flake8 -v page_analyzer

start_postgres:
	echo "123" | sudo -S -k service postgresql start

build: start_postgres
	./build.sh
