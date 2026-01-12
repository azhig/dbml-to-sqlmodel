.PHONY: help install generate preview info run dev clean db-reset format lint test

# Цвета для вывода
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Показать это сообщение помощи
	@echo "$(GREEN)Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить зависимости
	uv sync

# CLI Commands (новый способ - рекомендуется)

cli: ## Запустить интерактивное меню CLI
	uv run dbml-crud

generate: ## Сгенерировать FastAPI приложение из schema.dbml
	uv run dbml-crud generate schemas/schema.dbml -o output
	@echo "$(GREEN)✓ Приложение успешно сгенерировано в output/$(NC)"

preview: ## Показать diff изменений без записи файлов
	uv run dbml-crud preview schemas/schema.dbml -o output

info: ## Показать файлы и несоответствия генерации
	uv run dbml-crud info schemas/schema.dbml

run: ## Запустить сервер (production режим)
	cd output && uv run python main.py

dev: ## Запустить сервер в режиме разработки с hot-reload
	cd output && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001

clean: ## Удалить сгенерированные файлы и кэш
	rm -rf output/
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Временные файлы удалены$(NC)"

db-reset: ## Удалить базу данных (для пересоздания схемы)
	rm -f output/database.db
	@echo "$(GREEN)✓ База данных удалена$(NC)"

format: ## Отформатировать код с помощью ruff
	uv run ruff format .
	@echo "$(GREEN)✓ Код отформатирован$(NC)"

lint: ## Проверить код линтером
	uv run ruff check .

test: ## Запустить тесты
	uv run pytest tests/ -v

test-watch: ## Запустить тесты в режиме watch
	uv run pytest-watch tests/ -v

# Комплексные команды

fresh: clean generate ## Полная перегенерация: удалить старое + сгенерировать новое
	@echo "$(GREEN)✓ Приложение полностью перегенерировано$(NC)"

restart: db-reset run ## Пересоздать БД и запустить сервер

full-reset: clean db-reset generate run ## Полный сброс: удалить всё, сгенерировать и запустить
	@echo "$(GREEN)✓ Полный сброс выполнен$(NC)"
