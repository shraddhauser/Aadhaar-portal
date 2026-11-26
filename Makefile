# Shortcuts for common tasks (Linux/macOS, or Windows with make installed).
# Each target is a plain command; the README lists the same commands.
PYTHON ?= python

.PHONY: install install-dev setup run test lint

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

setup:          ## build the database from data/*.csv and create an admin
	$(PYTHON) scripts/setup_complete.py

run:
	$(PYTHON) -m uvicorn backend.main:app --port 8000 --reload

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check backend scripts tests
