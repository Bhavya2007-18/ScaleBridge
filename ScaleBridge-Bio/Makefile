.PHONY: help install test test-backend test-frontend lint dev run-backend run-frontend docker-up docker-down clean

help:
	@echo "ScaleBridge Bio Development Makefile"
	@echo "Commands:"
	@echo "  install        Install both backend and frontend dependencies"
	@echo "  test           Run all tests (backend pytest + frontend typecheck)"
	@echo "  test-backend   Run backend pytest with coverage"
	@echo "  test-frontend  Run frontend typecheck and build"
	@echo "  lint           Run linting checks (ruff, prettier)"
	@echo "  dev            Run both backend and frontend in local dev mode"
	@echo "  docker-up      Start containerized stack via docker compose"
	@echo "  docker-down    Tear down containerized stack"
	@echo "  clean          Remove temporary caches and build artifacts"

install:
	cd backend && pip install -r requirements-dev.txt && pip install -e .
	cd frontend && npm install

test: test-backend test-frontend

test-backend:
	cd backend && pytest --cov=app

test-frontend:
	cd frontend && npm run typecheck

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

clean:
	rm -rf backend/.pytest_cache backend/.ruff_cache backend/__pycache__
	rm -rf frontend/node_modules frontend/dist frontend/.next
	rm -rf var/
