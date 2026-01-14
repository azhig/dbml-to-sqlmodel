```
██████╗ ██████╗ ███╗   ███╗██╗         ████████╗ ██████╗
██╔══██╗██╔══██╗████╗ ████║██║         ╚══██╔══╝██╔═══██╗
██║  ██║██████╔╝██╔████╔██║██║            ██║   ██║   ██║
██║  ██║██╔══██╗██║╚██╔╝██║██║            ██║   ██║   ██║
██████╔╝██████╔╝██║ ╚═╝ ██║███████╗       ██║   ╚██████╔╝
╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝       ╚═╝    ╚═════╝

███████╗ ██████╗ ██╗     ███╗   ███╗ ██████╗ ██████╗ ███████╗██╗
██╔════╝██╔═══██╗██║     ████╗ ████║██╔═══██╗██╔══██╗██╔════╝██║
███████╗██║   ██║██║     ██╔████╔██║██║   ██║██║  ██║█████╗  ██║
╚════██║██║▄▄ ██║██║     ██║╚██╔╝██║██║   ██║██║  ██║██╔══╝  ██║
███████║╚██████╔╝███████╗██║ ╚═╝ ██║╚██████╔╝██████╔╝███████╗███████╗
╚══════╝ ╚══▀▀═╝ ╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚══════╝
```

<p align="center" markdown=1>
  <a href="https://github.com/azhig/dbml_to_crud/actions/workflows/tests.yml">
    <img src="https://github.com/azhig/dbml_to_crud/actions/workflows/tests.yml/badge.svg" alt="Tests"/>
  </a>
  <a href="https://codecov.io/gh/azhig/dbml_to_crud">
    <img src="https://codecov.io/gh/azhig/dbml_to_crud/branch/main/graph/badge.svg" alt="Coverage"/>
  </a>
  <img src="https://img.shields.io/badge/python-3.11%20|%203.12%20|%203.13-blue" alt="Python Versions"/>
  <a href="https://github.com/azhig/dbml_to_crud/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/azhig/dbml_to_crud" alt="License: MIT"/>
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"/>
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="Pre-commit"/>
  </a>
  <img src="https://img.shields.io/badge/code%20style-ruff-000000.svg" alt="Code style: ruff"/>
  <img src="https://img.shields.io/badge/type%20checked-mypy-blue.svg" alt="Type checked: mypy"/>
</p>

**Generate FastAPI + SQLModel + FastCRUD + SQLAdmin from DBML schema**

## Features

- Generate SQLModel models from DBML schema
- Auto-create CRUD routers with FastCRUD
- Generate FastAPI application with ready-to-use endpoints
- Optional SQLAdmin panel
- Preview mode to review changes before applying
- Protect user modifications in generated files
- Interactive CLI and direct commands

## Requirements

- Python 3.11+
- uv (recommended) or any Python environment manager

## Installation

### For Code Generation Only

```bash
pip install dbml-to-sqlmodel
```

### For Running Generated Applications

```bash
# Install with runtime dependencies
pip install dbml-to-sqlmodel[runtime]

# Or install runtime dependencies separately in your project
pip install fastapi[all] sqlmodel fastcrud sqladmin aiosqlite
```

## Quick Start

### 1. Create a DBML schema

Create a `schema.dbml` file with your database structure:

```dbml
Table users {
  id integer [primary key]
  username varchar(255) [not null, unique]
  email varchar(255) [not null, unique]
  created_at timestamp [default: `now()`]
}

Table posts {
  id integer [primary key]
  title varchar(255) [not null]
  content text
  user_id integer [ref: > users.id]
  created_at timestamp [default: `now()`]
}
```

### 2. Generate the application

```bash
dbml-to-sqlmodel generate schema.dbml -o output
```

### 3. Setup environment

```bash
cd output
echo "DATABASE_URL=sqlite+aiosqlite:///./database.db" > .env

# Install runtime dependencies if not already installed
pip install dbml-to-sqlmodel[runtime]
```

### 4. Run the application

```bash
python main.py
```

### 5. Open in browser

- API documentation: `http://localhost:8001/docs`
- Admin panel: `http://localhost:8001/admin`

## Generated Structure

The generator creates a modular project where each table has its own directory:

```
output/
├── main.py              # FastAPI application
├── admin.py             # SQLAdmin configuration
├── requirements.txt     # Dependencies
└── models/
    ├── __init__.py      # Exports all models
    ├── users/
    │   ├── model.py     # SQLModel classes (Users, UsersCreate, UsersUpdate)
    │   ├── crud.py      # FastCRUD router
    │   └── __init__.py
    ├── posts/
    │   ├── model.py
    │   ├── crud.py
    │   └── __init__.py
    └── ... (one directory per table)
```

For detailed structure documentation, see [CLI_GUIDE.md](CLI_GUIDE.md#generated-project-structure).

## CLI Usage

For complete CLI documentation, see [CLI_GUIDE.md](CLI_GUIDE.md).

### Quick Commands

```bash
# Interactive CLI mode
dbml-to-sqlmodel

# Generate application
dbml-to-sqlmodel generate schema.dbml -o output

# Preview changes
dbml-to-sqlmodel preview schema.dbml

# Show schema info
dbml-to-sqlmodel info schema.dbml

# Reverse: code to DBML
dbml-to-sqlmodel code-to-dbml output -o schema.dbml
```

## Configuration

### Environment Variables

Create a `.env` file in your project directory:

```env
DATABASE_URL=sqlite+aiosqlite:///./database.db
```

### SQLAdmin Authentication

To enable admin panel authentication:

```bash
dbml-to-sqlmodel generate schema.dbml --admin-auth
```

Add to your `.env` file:

```env
ADMIN_USER=admin
ADMIN_PASS=your-secure-password
ADMIN_SECRET=your-secret-key-must-be-at-least-32-characters-long
```

For more configuration options, see [CLI_GUIDE.md](CLI_GUIDE.md).

## Protecting Your Modifications

If you modify generated files and want to prevent them from being overwritten on regeneration, add this comment at the top of the file:

```python
# USER_MODIFIED
```

Files with this marker will be protected during regeneration unless you use the `--force` flag.

## Development

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Generate HTML coverage report
make coverage-html
# Open htmlcov/index.html in browser
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint
```

## Usage Examples

See [CLI_GUIDE.md](CLI_GUIDE.md) for complete examples and workflows.

## Table Relationships

Supported relationship types:

- **One-to-Many**: `ref: > table.column`
- **Many-to-One**: `ref: < table.column`
- **One-to-One**: `ref: - table.column`

Example:

```dbml
Table posts {
  id integer [primary key]
  user_id integer [ref: > users.id]  // Many-to-One
}
```

## License

MIT
