.PHONY: help install dev-install test lint format clean build run docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean temporary files"
	@echo "  build        - Build the application"
	@echo "  run          - Run the development server"
	@echo "  docker-build - Build Docker images"
	@echo "  docker-up    - Start Docker services"
	@echo "  docker-down  - Stop Docker services"

# Installation
install:
	pip install -r requirements.txt

dev-install: install
	pip install -e ".[dev,docs,monitoring]"
	pre-commit install

# Testing
test:
	pytest

test-cov:
	pytest --cov=backend --cov-report=html

test-watch:
	pytest -f

# Code quality
lint:
	flake8 backend/
	mypy backend/
	black --check backend/

format:
	black backend/
	isort backend/

# Cleaning
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Building
build:
	python setup.py sdist bdist_wheel

# Development
run:
	python -m backend.app

run-dev:
	uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

run-worker:
	celery -A backend.app.celery worker --loglevel=info

run-beat:
	celery -A backend.app.celery beat --loglevel=info

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f

# Database
db-migrate:
	alembic upgrade head

db-reset:
	alembic downgrade base
	alembic upgrade head

# ML Models
train-model:
	python -m ml_core.training_pipeline.train_production_model

train-improved-model:
	python -m ml_core.training_pipeline.train_improved_production_model

# Frontend
frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm start

# Production
deploy:
	docker-compose -f docker-compose.prod.yml up -d

deploy-build:
	docker-compose -f docker-compose.prod.yml build

# Monitoring
logs:
	tail -f logs/app.log

monitor:
	python -m backend.monitoring.monitor

# Security
security-check:
	bandit -r backend/
	safety check

# Performance
benchmark:
	python -m backend.benchmarks.prediction_benchmark

profile:
	python -m backend.profiling.profile_prediction

# Documentation
docs-build:
	mkdocs build

docs-serve:
	mkdocs serve

# All checks
check: lint test security-check
	@echo "All checks passed!"

# CI/CD
ci-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

ci-test:
	pytest --cov=backend --cov-report=xml

ci-lint:
	flake8 backend/
	mypy backend/
	black --check backend/

ci-build:
	python setup.py sdist bdist_wheel

# Release
release: clean test build
	@echo "Ready for release!"
