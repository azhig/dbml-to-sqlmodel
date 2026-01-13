.PHONY: help install generate preview info run dev clean db-reset format lint test

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
	uv run dbml-code

generate: ## Generate FastAPI app from schema.dbml
	uv run dbml-code generate examples/schema.dbml -o output
	@echo "$(GREEN)OK: app generated in output/$(NC)"

preview: ## Show diff without writing files
	uv run dbml-code preview examples/schema.dbml -o output

info: ## Show generated files and mismatches
	uv run dbml-code info examples/schema.dbml

run: ## Run server (production)
	cd output && uv run python main.py

dev: ## Run server in development mode (hot reload)
	cd output && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

clean: ## Remove generated files and caches
	rm -rf output/
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)OK: temporary files removed$(NC)"

db-reset: ## Remove database (to recreate schema)
	rm -f output/database.db
	@echo "$(GREEN)OK: database removed$(NC)"

format: ## Format code with ruff
	uv run ruff format .
	@echo "$(GREEN)OK: code formatted$(NC)"

lint: ## Lint code
	uv run ruff check .

test: ## Run tests
	uv run pytest tests/ -v

test-watch: ## Run tests in watch mode
	uv run pytest-watch tests/ -v

# Compound commands

fresh: clean generate ## Full regeneration: remove old + generate new
	@echo "$(GREEN)OK: app fully regenerated$(NC)"

restart: db-reset run ## Recreate DB and start server

full-reset: clean db-reset generate run ## Full reset: remove all, generate, and run
	@echo "$(GREEN)OK: full reset complete$(NC)"
