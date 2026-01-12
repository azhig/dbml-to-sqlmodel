# DBML to CRUD Generator

Modern CLI tool for generating complete FastAPI applications with admin panel from DBML database schema definitions.

## Features

- **🎯 Interactive CLI** - Beautiful interactive menu with arrow key navigation
- **👁️ Auto-Preview** - Automatically shows model.py diffs before applying changes
- **🔒 Smart Protection** - Automatically detects and protects user-modified files
- **📊 Report** - List generated files and show mismatches vs current output
- **🔁 Code → DBML** - Generate DBML from output models with a diff before saving
- **🚀 Full Stack** - Generates SQLModel models, FastCRUD routers, and SQLAdmin views
- **⚡ Fast** - Built with modern async Python stack

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd dbml_to_crud

# Install dependencies
make install
```

### Basic Usage

```bash
# Run interactive CLI (рекомендуется!)
uv run dbml-crud

# Интерактивное меню позволяет:
# - Выбирать команды стрелками ↑↓
# - Подтверждать выбор Enter
# - При генерации автоматически показывает diff
# - Запрашивает подтверждение перед применением изменений
```

### Alternative: Direct Commands

Вы также можете использовать прямые команды:

```bash
# Generate FastAPI app from schema
make generate
# or: uv run dbml-crud generate schemas/schema.dbml -o output

# Preview changes (shows diff)
make preview
# or: uv run dbml-crud preview schemas/schema.dbml -o output

# Show generated files and mismatches
make info
# or: uv run dbml-crud info schemas/schema.dbml

# Run the generated application
make dev
# or: cd output && uv run python main.py
```

## 📚 Документация

- **[DEMO.md](DEMO.md)** - 🎬 Визуальная демонстрация работы CLI
- **[INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md)** - 📖 Подробное руководство по интерактивному режиму
- **[EXAMPLES.md](EXAMPLES.md)** - 💡 Примеры использования всех команд

## CLI Commands

### 🎯 Интерактивный режим (рекомендуется)

Запустите без аргументов для интерактивного меню:

```bash
uv run dbml-crud
```

**Возможности:**
- Навигация стрелками ↑↓
- Автоматический preview перед генерацией
- Подтверждение изменений
- Защита пользовательских файлов
- Continuous workflow

**Подробнее:** См. [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md)

---

### Прямые команды (опционально)

Также доступны прямые команды для автоматизации:

### 1. `generate` - Generate FastAPI Application

Creates a complete FastAPI application from your DBML schema.

```bash
uv run dbml-crud generate <schema-file> [OPTIONS]

Options:
  -o, --output PATH    Output directory (default: output)
  -f, --force          Overwrite user-modified files
  --help               Show this message and exit
```

**Features:**
- Automatically detects existing files
- Protects files marked with `USER_MODIFIED`
- Shows file status table (new/modified/unchanged/protected)
- Progress indicators for generation steps

**Example:**
```bash
# Generate with default output directory
uv run dbml-crud generate schemas/schema.dbml

# Custom output directory
uv run dbml-crud generate schemas/schema.dbml -o my_app

# Force overwrite protected files
uv run dbml-crud generate schemas/schema.dbml --force

```

### 2. `preview` - Show Changes Before Applying

Preview what would change without modifying any files. Shows unified diff for `models/*/model.py`.

```bash
uv run dbml-crud preview <schema-file> [OPTIONS]

Options:
  -o, --output PATH    Output directory (default: output)
  -a, --all            Show unchanged files too
  -n, --new            Show content of new files
  --help               Show this message and exit
```

**Features:**
- Unified diff view with syntax highlighting
- Protected file warnings
- Summary statistics (new/modified/unchanged/protected)
- No files are modified

**Example:**
```bash
# Show diff for modified model.py files
uv run dbml-crud preview schemas/schema.dbml

# Show all files including unchanged
uv run dbml-crud preview schemas/schema.dbml --all

# Show content of new files
uv run dbml-crud preview schemas/schema.dbml --new
```

### 3. `info` (Report) - Generated Files and Mismatches

Show the generated file list and any mismatches between generated output and existing files.

```bash
uv run dbml-crud info <schema-file> [OPTIONS]

Options:
  -o, --output PATH    Output directory (default: output)
  --help               Show this message and exit
```

**Features:**
- Status table for `models/*/model.py`
- Diff for modified model.py files
- Full content for new model.py files
- Summary counts

**Example:**
```bash
uv run dbml-crud info schemas/schema.dbml -o output
```

### 4. Code → DBML (Interactive)

Generate DBML from `output/models/`, show a diff, and optionally save via the interactive menu.

```bash
uv run dbml-crud
```

## Protecting User-Modified Files

The generator automatically protects files you've manually modified. To mark a file as user-modified, add this marker at the top:

```python
# USER_MODIFIED
# This file has custom changes

# Your code here...
```

**What happens:**
- Files with `USER_MODIFIED` marker are detected automatically
- They appear as "🔒 Protected" in status tables
- They are skipped during generation (unless `--force` is used)
- Preview command shows them with special warning

## Generated Application Structure

After running `generate`, you'll get:

```
output/
├── models/                  # SQLModel ORM models
│   ├── __init__.py
│   ├── <table_name>/
│   │   ├── __init__.py
│   │   ├── model.py         # Table, Create, Update schemas
│   │   └── crud.py          # FastCRUD router
│   └── ...
├── admin.py                 # SQLAdmin views
├── main.py                  # FastAPI application
├── requirements.txt         # Python dependencies
└── database.db             # SQLite database (created on first run)
```

## Makefile Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make cli            # Show CLI help

make generate       # Generate FastAPI app from schemas/schema.dbml
make preview        # Show diff without writing files
make info           # Show generated files and mismatches

make dev            # Run server with hot-reload (port 8001)
make run            # Run server (production mode)

make clean          # Remove output/ directory and cache
make db-reset       # Delete database for schema recreation
make fresh          # Clean + regenerate
make full-reset     # Complete reset: clean, db-reset, generate, run

make format         # Format code with ruff
make lint           # Lint code with ruff
make test           # Run tests
```

## Example Workflow

### 1. Design Your Schema

Create a DBML file (e.g., `schemas/my_app.dbml`):

```dbml
Table users {
  id serial [primary key]
  email text [unique, not null]
  name text [not null, note: "User's full name"]
  created_at timestamp [default: `now()`]
}

Table posts {
  id serial [primary key]
  user_id integer [ref: > users.id, not null]
  title text [not null]
  content text
  created_at timestamp [default: `now()`]
}
```

### 2. Inspect → Preview → Generate

```bash
# 1. Inspect schema
uv run dbml-crud info schemas/my_app.dbml -o my_app

# 2. Preview what will be generated
uv run dbml-crud preview schemas/my_app.dbml -o my_app

# 3. Generate application
uv run dbml-crud generate schemas/my_app.dbml -o my_app

# 4. Run development server
cd my_app && uv run uvicorn main:app --reload --port 8001
```

### 3. Access Your Application

- **API Docs**: http://localhost:8001/docs
- **Admin Panel**: http://localhost:8001/admin
- **API**: http://localhost:8001/

### 4. Customize Safely

```bash
# Edit a file
vim output/models/users/model.py

# Add protection marker at top:
# USER_MODIFIED

# Regenerate - your file is now protected!
uv run dbml-crud generate schemas/my_app.dbml -o my_app
```

## Architecture

### Key Design Decisions

- **Directory Separation**: Generator in `src/`, schemas in `schemas/`, output in `output/` (gitignored)
- **Schema Separation**: Each table gets Table, TableCreate, TableUpdate classes
- **SQLModel Relationships**: Foreign keys become `Relationship()` fields
- **File Protection**: `USER_MODIFIED` marker prevents overwrites
- **Admin Icons**: Auto-selected based on table name keywords

## Dependencies

Core stack:

- **FastAPI**: Web framework
- **SQLModel**: ORM (combines SQLAlchemy + Pydantic)
- **FastCRUD**: Automatic CRUD router generation
- **SQLAdmin**: Admin panel UI
- **PyDBML**: DBML parser
- **aiosqlite**: Async SQLite driver
- **Typer**: CLI framework
- **Rich**: Terminal formatting and colors

## Tips and Tricks

### Custom Database

Edit generated `main.py` to change database:

```python
# PostgreSQL
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

# MySQL
DATABASE_URL = "mysql+aiomysql://user:pass@localhost/dbname"
```

### Multiple Schemas

```bash
# Generate different apps from different schemas
uv run dbml-crud generate schemas/app1.dbml -o app1
uv run dbml-crud generate schemas/app2.dbml -o app2
```

## Troubleshooting

### Import Errors

```bash
uv sync
```

### Protected Files Not Detected

Make sure marker is at the very top:

```python
# USER_MODIFIED
# Must be first line!
```

### Database Locked

```bash
make db-reset
```

## License

[Add your license here]
