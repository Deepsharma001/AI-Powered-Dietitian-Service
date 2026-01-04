.DEFAULT_GOAL := help

help:
	@echo "Available targets:"
	@echo "  install      Install Python dependencies"
	@echo "  venv         Create virtualenv in .venv and install deps"
	@echo "  init-db      Initialize SQLite database and populate meals"
	@echo "  run          Run dev server (uvicorn --reload)"
	@echo "  run-prod     Run production server"
	@echo "  test         Run tests with pytest"
	@echo "  clean        Remove generated files (diet.db, pycache)"
	@echo "  freeze       Update requirements.txt"

install:
	python -m pip install --upgrade pip
	pip install -r requirements.txt

venv:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

init-db:
	python -c "from database import init_db; init_db(); print('database initialized')"

run:
	uvicorn main:app --reload

run-prod:
	uvicorn main:app --host 0.0.0.0 --port 8000

test:
	pytest -q

clean:
	rm -f diet.db
	find . -type d -name '__pycache__' -exec rm -rf {} +

freeze:
	pip freeze > requirements.txt
