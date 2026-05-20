.PHONY: all format lint test test-update-golden

all: lint test

format:
	poetry run ruff format .

lint:
	poetry run ruff check --fix .
	poetry run mypy .

test:
	poetry run pytest . -v

test-update-golden:
	poetry run pytest . -v --update-goldens
