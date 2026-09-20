PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python; fi)
COMPOSE ?= docker compose
export PYTHONPATH := .:src

.PHONY: install lint typecheck typecheck-web test test-all test-live eval eval-full up down migrate seed demo load-test load-test-locust run-api run-web audit

install:
	$(PYTHON) -m pip install -e ".[dev]"
	cd frontend && npm install

lint:
	ruff check src tests evaluation scripts
	ruff format --check src tests evaluation scripts

lint-fix:
	ruff check --fix src tests evaluation scripts
	ruff format src tests evaluation scripts

typecheck:
	mypy src

typecheck-web:
	cd frontend && npm run typecheck

audit:
	$(PYTHON) -m pip_audit

test:
	$(PYTHON) -m pytest -q --ignore=tests/integration

test-live:
	LIVE_HTTP=1 $(PYTHON) -m pytest -q tests/live tests/regression tests/agents

test-all:
	INTEGRATION=1 $(PYTHON) -m pytest -q

eval:
	$(PYTHON) -m evaluation.runners.harness --suite regression --out evaluation/reports/regression.json

eval-full:
	$(PYTHON) -m evaluation.runners.harness --suite full --out evaluation/reports/latest.json

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down -v

migrate:
	alembic upgrade head

seed:
	$(PYTHON) -m scripts.seed

demo:
	$(PYTHON) -m scripts.demo

run-api:
	$(PYTHON) -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8009

run-web:
	cd frontend && npm run dev

load-test:
	$(PYTHON) -m scripts.load_test --host http://127.0.0.1:8009 --users 20 --duration 20 --out evaluation/reports/load_stats.csv

load-test-locust:
	$(PYTHON) -m locust -f tests/load/locustfile.py --headless -u 20 -r 5 -t 20s --host http://127.0.0.1:8009 --csv evaluation/reports/load
