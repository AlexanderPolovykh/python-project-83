
install:
	poetry install

dev:
	poetry run flask --app page_analyzer:app run

TCP_PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(TCP_PORT) page_analyzer:app

lint:
	poetry run flake8 -v page_analyzer
