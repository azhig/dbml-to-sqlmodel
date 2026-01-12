# Changelog

## [Interactive CLI] - 2026-01-12

### 🎯 Interactive Menu Interface

#### Добавлено
- 🎯 **Interactive CLI Menu** - навигация стрелками ↑↓ и выбор Enter
- 🤖 **Auto-Preview on Generate** - автоматический показ diff перед генерацией
- ✅ **Confirmation Prompts** - подтверждение перед применением изменений
- 🔄 **Continuous Workflow** - возможность выполнять несколько операций подряд
- 🎨 **Rich formatting** - красивые таблицы, progress bars, цветной вывод
- 👁️ **Preview Mode** - просмотр diff перед применением изменений
- 📊 **Info Command** - инспекция DBML схемы без генерации
- 🔒 **File Protection** - автоматическая защита пользовательских файлов
- ⚡ **Progress Indicators** - индикаторы прогресса для длительных операций

#### Интерактивное меню
Теперь CLI работает как интерактивное приложение:
1. Запуск: `uv run dbml-crud` (без аргументов)
2. Выбор команды стрелками ↑↓
3. Подтверждение Enter
4. Интерактивные вопросы для каждой операции
5. При генерации **автоматически показывается diff**
6. Подтверждение перед применением изменений

#### Новые команды CLI

```bash
# Показать версию
uv run dbml-crud version

# Генерация с опциями
uv run dbml-crud generate schemas/schema.dbml [OPTIONS]
  -o, --output PATH    # Директория вывода
  -f, --force          # Перезаписать защищенные файлы
  -d, --dry-run        # Показать что будет сделано

# Предпросмотр изменений
uv run dbml-crud preview schemas/schema.dbml [OPTIONS]
  -a, --all            # Показать все файлы
  -n, --new            # Показать содержимое новых файлов

# Информация о схеме
uv run dbml-crud info schemas/schema.dbml [OPTIONS]
  -v, --verbose        # Детальная информация
```

#### Новые модули

- 📁 `src/dbml_to_crud/` - пакет CLI
  - `cli.py` - главный CLI модуль
  - `generator.py` - функции генерации
  - `utils.py` - утилиты (diff, защита файлов)
  - `commands/` - команды CLI
    - `generate.py` - команда генерации
    - `preview.py` - команда предпросмотра
    - `info.py` - команда информации

#### Возможности Preview Mode

- ✨ **Unified Diff** с подсветкой синтаксиса
- 📋 **File Status Table** - статус каждого файла (new/modified/unchanged/protected)
- 🔒 **Protected File Warnings** - предупреждения о защищенных файлах
- 📊 **Summary Statistics** - итоговая статистика изменений

#### Защита пользовательских файлов

```python
# Добавьте маркер в начало файла
# USER_MODIFIED
# This file has custom changes

# Ваш код...
```

**Функции защиты:**
- Автоматическое обнаружение маркера `USER_MODIFIED`
- Отображение защищенных файлов в статусе 🔒
- Пропуск при генерации (если не указан `--force`)
- Предупреждения в preview mode

#### Улучшения Makefile

```bash
make cli            # Показать CLI help
make generate       # Генерация через CLI
make preview        # Предпросмотр изменений
make info           # Информация о схеме
```

#### Новые зависимости

- `typer>=0.17.0` - CLI framework
- `rich>=14.0.0` - Terminal formatting
- `pydantic>=2.11.1` - Data validation
- `questionary>=2.0.0` - Interactive prompts and menus

#### Документация

- 📝 `README.md` - полностью обновлен с CLI документацией
- 📝 `EXAMPLES.md` - примеры использования всех команд CLI
- 📝 `MIGRATION.md` - добавлена секция о миграции на CLI

#### Breaking Changes

⚠️ **Изменение структуры пакета**

Старый импорт:
```python
from dbml_to_sqlmodel import parse_dbml
from generate_app import generate_all
```

Новый импорт:
```python
from dbml_to_crud.dbml_to_sqlmodel import parse_dbml
from dbml_to_crud.generator import generate_all_files
```

⚠️ **Рекомендуется использовать CLI**

Прямой вызов Python скриптов устарел:
```bash
# Старый способ (deprecated)
python src/generate_app.py schemas/schema.dbml -o output

# Новый способ (recommended)
uv run dbml-crud generate schemas/schema.dbml -o output
```

#### Миграция

См. [MIGRATION.md](MIGRATION.md#миграция-3-modern-cli-interface-январь-2026) и [EXAMPLES.md](EXAMPLES.md)

## [Modular Models] - 2026-01-12

### Новая модульная структура моделей

#### Добавлено
- 🏗️ Модульная структура моделей: каждая модель в отдельной директории
- 📁 `models/{table_name}/model.py` - SQLModel классы для каждой модели
- 📁 `models/{table_name}/crud.py` - CRUD роутер для каждой модели
- 📁 `models/{table_name}/__init__.py` - экспорты для каждой модели
- 📝 `models/__init__.py` - корневой модуль со всеми экспортами
- 🔧 Фабричные функции `create_{table_name}_router()` для инициализации роутеров с зависимостями

#### Структура моделей
Каждая модель теперь находится в отдельном каталоге:
```
models/
├── __init__.py                    # Корневой модуль
├── typical_scenario/
│   ├── __init__.py               # Экспорты модели
│   ├── model.py                  # SQLModel классы
│   └── crud.py                   # CRUD роутер
└── roles/
    ├── __init__.py
    ├── model.py
    └── crud.py
```

#### Добавлено в src/dbml_to_sqlmodel.py
- ✅ Функция `generate_single_model()` для генерации отдельной модели
- ✅ Поддержка генерации модели в изолированном файле
- ✅ Автоматический импорт связанных моделей через `TYPE_CHECKING` блок
- ✅ Избежание циклических импортов с использованием forward references

#### Изменено в src/generate_app.py
- ♻️ `generate_crud_router()` переименована в `generate_crud_router()` и генерирует отдельный роутер
- ➕ Добавлена `generate_model_init()` - генерация __init__.py для каждой модели
- ➕ Добавлена `generate_models_root_init()` - генерация корневого __init__.py
- 🔄 Изменена структура main.py для работы с модульными роутерами
- 🔄 Обновлен admin.py для импорта из модульной структуры

### Преимущества модульной структуры

1. **Изоляция моделей**: Каждая модель в своём пакете
2. **Читаемость кода**: Легко найти код конкретной модели
3. **Кастомизация**: Удобно добавлять специфичную логику к модели
4. **Масштабируемость**: Подходит для проектов с большим количеством моделей
5. **Командная работа**: Меньше конфликтов в git при одновременной работе

## [Restructured] - 2026-01-12

### Изменения в структуре проекта

### Изменения в структуре проекта

#### Добавлено
- 📁 `src/` - директория для исходного кода генератора
- 📁 `schemas/` - директория для DBML схем
- 📁 `output/` - директория для сгенерированных файлов (gitignored)
- 📁 `tests/` - директория для unit-тестов
- ✅ `tests/test_parser.py` - тесты для DBML парсера
- 📝 `README.md` - полная документация проекта на русском
- 📝 `CLAUDE.md` - документация для Claude Code с архитектурой
- 📝 `MIGRATION.md` - руководство по миграции на новую структуру
- 📝 `schemas/example_blog.dbml` - пример схемы блога
- 🛠️ Makefile с командами разработки

#### Изменено
- ♻️ Перенесены `dbml_to_sqlmodel.py` и `generate_app.py` в `src/`
- ♻️ Перенесен `schema.dbml` в `schemas/`
- 🔧 `generate_app.py` теперь поддерживает параметр `-o/--output` для указания директории вывода
- 🔧 `.gitignore` обновлен для новой структуры
- 🔧 `Makefile` обновлен для работы с новыми путями
- 🎨 Команда `make dev` теперь запускает сервер на порту 8001

#### Улучшения
- 🎯 Четкое разделение исходников генератора и сгенерированных файлов
- 🧹 Сгенерированные файлы больше не засоряют git
- 📦 Возможность работы с множественными DBML схемами
- ✨ Добавлена поддержка unit-тестирования
- 🚀 Упрощен workflow разработки через Makefile
- 📖 Улучшена документация проекта

### Новые команды Makefile

```bash
make help           # Показать все команды
make install        # Установить зависимости
make generate       # Сгенерировать приложение
make dev            # Запустить с hot-reload (port 8001)
make run            # Запустить production
make clean          # Удалить сгенерированные файлы
make db-reset       # Удалить базу данных
make fresh          # Пересоздать всё
make full-reset     # Полный сброс
make format         # Отформатировать код
make lint           # Проверить код
make test           # Запустить тесты
```

### Breaking Changes

⚠️ **Изменение путей для генерации**

Старая команда:
```bash
python generate_app.py schema.dbml
```

Новая команда:
```bash
make generate
# или
uv run python src/generate_app.py schemas/schema.dbml -o output
```

⚠️ **Изменение расположения файлов**

- Генератор: `src/generate_app.py` (было: `generate_app.py`)
- Схемы: `schemas/schema.dbml` (было: `schema.dbml`)
- Вывод: `output/` (было: корень проекта)

### Миграция

См. [MIGRATION.md](MIGRATION.md) для подробного руководства по переходу на новую структуру.

### Технические детали

- Python >= 3.11
- Использует `uv` для управления зависимостями
- Все тесты проходят успешно (4 теста)
- Линтинг через `ruff`
- Форматирование через `ruff format`
