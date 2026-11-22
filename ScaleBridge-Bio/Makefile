# ScaleBridge Bio — Automation Makefile (Local ScaleBridge-Bio directory)
# Domain F Deliverable (Owner: Person 4 - Reporting, DevOps and Quality Lead)

.PHONY: help install test test-science test-api test-reporting test-cov lint format typecheck run docker-up docker-down backup clean

help:
	@echo "ScaleBridge Bio Development Commands:"
	@echo "  make install        Install backend and dev dependencies"
	@echo "  make test           Run all pytest test suites"
	@echo "  make test-science   Run scientific golden-vector tests (Person 1)"
	@echo "  make test-api       Run API workflow integration tests (Person 2 & 3)"
	@echo "  make test-reporting Run PDF report and generation tests (Person 4)"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make lint           Check code with Ruff"
	@echo "  make format         Auto-format code with Ruff"
	@echo "  make typecheck      Run Mypy static type analysis"
	@echo "  make run            Start local FastAPI backend server"
	@echo "  make docker-up      Start complete local Docker Compose stack"
	@echo "  make docker-down    Stop Docker Compose stack"
	@echo "  make backup         Create a verified database backup"
	@echo "  make clean          Remove cache, build, and test artifacts"

install:
	pip install --upgrade pip
	pip install -e "backend[dev]"

test:
	pytest backend/

test-science:
	pytest backend/scalebridge_science/tests/

test-api:
	pytest backend/tests/test_api_workflow.py

test-reporting:
	pytest backend/tests/test_reporting.py

test-cov:
	pytest backend/ --cov=backend/app --cov=backend/scalebridge_science --cov-report=term-missing

lint:
	ruff check backend/

format:
	ruff format backend/

typecheck:
	mypy backend/scalebridge_science backend/app --ignore-missing-imports

run:
	cd backend && uvicorn app.main:app --reload --port 8000

docker-up:
	docker compose up -d

docker-down:
	docker compose down

backup:
	python scripts/backup_db.py --verify

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf backend/.coverage backend/coverage.xml
