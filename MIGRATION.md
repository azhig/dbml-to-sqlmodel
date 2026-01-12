# Руководство по миграции структуры проекта

## История изменений

### Миграция 3: Modern CLI Interface (Январь 2026)

Добавлен современный CLI с командами `generate`, `preview`, `info` вместо прямого вызова Python скриптов.

#### Старый способ:
```bash
python src/generate_app.py schemas/schema.dbml -o output
```

#### Новый способ:
```bash
# Через CLI
uv run dbml-crud generate schemas/schema.dbml -o output

# Или через make
make generate
```

#### Новые возможности:

1. **Preview Mode** - просмотр diff перед применением:
```bash
uv run dbml-crud preview schemas/schema.dbml
```

2. **Schema Info** - инспекция схемы без генерации:
```bash
uv run dbml-crud info schemas/schema.dbml --verbose
```

3. **Защита пользовательских файлов**:
```python
# USER_MODIFIED
# Этот файл защищен от перезаписи
```

4. **Красивый интерфейс** с таблицами статусов, progress bars, и цветным diff

#### Миграция:

Старые команды продолжают работать, но рекомендуется использовать новый CLI:

```bash
# Было
python src/generate_app.py schemas/schema.dbml -o output

# Стало
uv run dbml-crud generate schemas/schema.dbml -o output
make generate  # или через make
```

### Миграция 2: Модульная структура моделей (Январь 2026)

Каждая модель теперь находится в отдельном каталоге со своими файлами.

#### Структура до миграции 2:
```
output/
├── models.py              # Все модели в одном файле
├── crud/
│   └── __init__.py       # Все CRUD роутеры в одном файле
├── admin.py
├── main.py
└── database.db
```

#### Структура после миграции 2:
```
output/
├── models/
│   ├── __init__.py                    # Корневой модуль
│   ├── typical_scenario/
│   │   ├── __init__.py               # Экспорты модели
│   │   ├── model.py                  # SQLModel классы
│   │   └── crud.py                   # CRUD роутер
│   ├── roles/
│   │   ├── __init__.py
│   │   ├── model.py
│   │   └── crud.py
│   └── ... (для каждой таблицы)
├── admin.py
├── main.py
└── database.db
```

**Преимущества модульной структуры:**
- ✅ Каждая модель изолирована в своём пакете
- ✅ Легко найти код конкретной модели
- ✅ Удобно добавлять кастомную логику к конкретной модели
- ✅ Меньше конфликтов при работе в команде (git)
- ✅ Масштабируемость для больших проектов

### Миграция 1: Разделение src/schemas/output

Проект был реорганизован для лучшей структуры и разделения исходного кода генератора и сгенерированных файлов.

#### Старая структура (до миграции 1):
```
dbml_to_crud/
├── dbml_to_sqlmodel.py
├── generate_app.py
├── schema.dbml
├── main.py              # Сгенерированные файлы
├── models.py            # в корне проекта
├── admin.py
├── crud/
└── database.db
```

#### Новая структура (после миграции 1):
```
dbml_to_crud/
├── src/                 # Исходники генератора
│   ├── dbml_to_sqlmodel.py
│   └── generate_app.py
├── schemas/             # DBML схемы
│   └── schema.dbml
├── output/              # Сгенерированные файлы (gitignored)
│   ├── models/          # (после миграции 2)
│   ├── main.py
│   ├── admin.py
│   └── database.db
└── tests/               # Тесты
    ├── __init__.py
    └── test_parser.py
```

## Детали модульной структуры

### Структура каждого модуля модели

#### `models/{table_name}/model.py`
Содержит:
- SQLModel класс для ORM (с `table=True`)
- Create схему для POST запросов (BaseModel)
- Update схему для PATCH запросов (BaseModel, все поля Optional)
- Relationship определения для связей с другими таблицами
- Импорты связанных моделей через `TYPE_CHECKING` блок (избегает циклических импортов)

Пример модели с relationships:
```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..roles.model import Roles

class Competencies(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key='roles.id')

    role: "Roles" = Relationship()
```

#### `models/{table_name}/crud.py`
Содержит:
- Фабричную функцию `create_{table_name}_router(get_session_func)` для создания CRUD роутера
- Эта функция принимает `get_session` как параметр и возвращает настроенный роутер

#### `models/{table_name}/__init__.py`
Экспортирует:
- Все классы модели (Model, Create, Update)
- Фабричную функцию для создания роутера

### Изменения в main.py

Теперь main.py:
1. Импортирует фабричные функции создания роутеров из каждого модуля
2. Вызывает эти функции, передавая `get_session` как зависимость
3. Регистрирует созданные роутеры в FastAPI приложении

Пример:
```python
from models.typical_scenario import create_typical_scenario_router

# Создание роутера с сессией
typical_scenario_router = create_typical_scenario_router(get_session)

# Регистрация роутера
app.include_router(typical_scenario_router)
```

### Обратная совместимость

Можно импортировать модели через корневой `models/__init__.py`:
```python
from models import Typical_scenario, Roles, create_typical_scenario_router
```

Это сохраняет совместимость с кодом, который ранее импортировал из `models.py`.

## Преимущества новой структуры

1. **Четкое разделение**: Исходный код генератора отделен от сгенерированных файлов
2. **Модульность**: Каждая модель изолирована в своём пакете
3. **Множественные схемы**: Возможность хранить несколько DBML схем в `schemas/`
4. **Чистый git**: Сгенерированные файлы в `output/` игнорируются git
5. **Тестирование**: Добавлена структура для unit-тестов
6. **Гибкость**: Генератор может выводить в любую директорию
7. **Масштабируемость**: Легко работать с большим количеством моделей

## Команды после миграции

### Старые команды
```bash
python generate_app.py schema.dbml
python main.py
```

### Новые команды
```bash
# Через Makefile (рекомендуется)
make generate
make dev

# Или вручную
uv run python src/generate_app.py schemas/schema.dbml -o output
cd output && uv run python main.py
```

## Что делать, если у вас есть изменения в сгенерированных файлах

Если вы внесли изменения в `main.py`, `models.py`, `admin.py` или `crud/`:

1. **Сохраните изменения**: Скопируйте ваши модификации
2. **Обновите DBML**: Перенесите изменения схемы в DBML файл
3. **Регенерируйте**: Запустите `make generate`
4. **Примените кастомизации**: Добавьте ваши изменения обратно (если они не относятся к схеме)

## Рекомендации

- ❌ **Не редактируйте** файлы в `output/` напрямую
- ✅ **Редактируйте** DBML схемы в `schemas/`
- ✅ **Регенерируйте** приложение после изменения схемы
- ✅ **Добавляйте** кастомную логику в отдельные модули

## Работа с несколькими схемами

Теперь вы можете работать с несколькими проектами:

```bash
# Схема для проекта A
uv run python src/generate_app.py schemas/project_a.dbml -o output_a

# Схема для проекта B
uv run python src/generate_app.py schemas/project_b.dbml -o output_b
```

## Обновление .gitignore

Убедитесь, что ваш `.gitignore` содержит:

```gitignore
/output/
*.db
*.db-journal
```

## Вопросы и поддержка

См. [CLAUDE.md](CLAUDE.md) для детальной документации по архитектуре проекта.
