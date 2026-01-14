.PHONY: help install cli generate preview info run dev clean db-reset format format-imports lint lint-fix typecheck check pre-commit pre-commit-install fresh restart full-reset

# Output colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

# CLI commands (recommended)

cli: ## Run interactive CLI
	uv run dbml-to-sqlmodel

generate: ## Generate FastAPI app from schema.dbml
	uv run dbml-to-sqlmodel generate examples/schema.dbml -o output
	@echo "$(GREEN)OK: app generated in output/$(NC)"

preview: ## Show diff without writing files
	uv run dbml-to-sqlmodel preview examples/schema.dbml -o output

info: ## Show generated files and mismatches
	uv run dbml-to-sqlmodel info examples/schema.dbml

run: ## Run server (production)
	cd output && uv run python main.py

dev: ## Run server in development mode (hot reload)
	cd output && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

clean: ## Remove generated files and caches
	rm -rf output/
	rm -rf __pycache__ .pytest_cache .ruff_cache htmlcov/ .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)OK: temporary files removed$(NC)"

db-reset: ## Remove database (to recreate schema)
	rm -f output/database.db
	@echo "$(GREEN)OK: database removed$(NC)"

format-imports: ## Sort and organize imports
	uv run ruff check . --select I --fix
	@echo -e "$(GREEN)OK: imports sorted$(NC)"

format: ## Format code with ruff (includes import sorting)
	uv run ruff check . --select I --fix
	uv run ruff format .
	@echo -e "$(GREEN)OK: code formatted and imports sorted$(NC)"

lint: ## Lint code
	uv run ruff check .

lint-fix: ## Lint and auto-fix code
	uv run ruff check . --fix
	@echo -e "$(GREEN)OK: linting issues fixed$(NC)"

typecheck: ## Run type checking with mypy
	uv run mypy src/dbml_to_sqlmodel

check: format lint typecheck test ## Run all checks (format, lint, typecheck, test)
	@echo -e "$(GREEN)OK: all checks passed$(NC)"

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install
	@echo "$(GREEN)OK: pre-commit hooks installed$(NC)"

pre-commit: ## Run pre-commit on all files
	uv run pre-commit run --all-files

test: ## Run tests
	uv run pytest tests/ -v

coverage: ## Run tests with coverage report in terminal
	uv run pytest tests/ --cov=src/dbml_to_sqlmodel --cov-report=term-missing -v
	@echo "$(GREEN)Coverage report generated$(NC)"

coverage-html: ## Generate HTML coverage report
	uv run pytest tests/ --cov=src/dbml_to_sqlmodel --cov-report=html --cov-report=term-missing -v
	@echo "$(GREEN)HTML coverage report generated in htmlcov/index.html$(NC)"
	@echo "Open it with: $(YELLOW)xdg-open htmlcov/index.html$(NC)"

coverage-report: coverage-html ## Alias for coverage-html

# Compound commands

fresh: clean generate ## Full regeneration: remove old + generate new
	@echo "$(GREEN)OK: app fully regenerated$(NC)"

restart: db-reset run ## Recreate DB and start server

full-reset: clean db-reset generate run ## Full reset: remove all, generate, and run
	@echo "$(GREEN)OK: full reset complete$(NC)"
