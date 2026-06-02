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
  <a href="https://pypi.org/project/dbml-to-sqlmodel/">
    <img src="https://img.shields.io/pypi/v/dbml-to-sqlmodel.svg" alt="PyPI version"/>
  </a>
  <a href="https://pypi.org/project/dbml-to-sqlmodel/">
    <img src="https://img.shields.io/pypi/pyversions/dbml-to-sqlmodel.svg" alt="Python Versions"/>
  </a>
  <a href="https://github.com/azhig/dbml-to-sqlmodel/actions/workflows/tests.yml">
    <img src="https://github.com/azhig/dbml-to-sqlmodel/actions/workflows/tests.yml/badge.svg" alt="Tests"/>
  </a>
  <a href="https://codecov.io/gh/azhig/dbml-to-sqlmodel">
    <img src="https://codecov.io/gh/azhig/dbml-to-sqlmodel/branch/main/graph/badge.svg" alt="Coverage"/>
  </a>
  <a href="https://github.com/azhig/dbml-to-sqlmodel/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/azhig/dbml-to-sqlmodel" alt="License: MIT"/>
  </a>
  <a href="https://github.com/astral-sh/ruff">
    <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"/>
  </a>
  <a href="https://github.com/pre-commit/pre-commit">
    <img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="Pre-commit"/>
  </a>
  <img src="https://img.shields.io/badge/type%20checked-mypy-blue.svg" alt="Type checked: mypy"/>
</p>

**Generate FastAPI + SQLModel + FastCRUD + SQLAdmin applications from a DBML schema.**

`dbml-to-sqlmodel` turns a [DBML](https://dbml.org/) database schema into a ready-to-run,
modular FastAPI project: SQLModel models, FastCRUD routers, an optional SQLAdmin panel,
and a wired-up application — in a single command.

## Features

- Generate SQLModel models from a DBML schema
- Auto-generate CRUD routers powered by [FastCRUD](https://github.com/igorbenav/fastcrud)
- Produce a FastAPI application with ready-to-use endpoints
- Optional [SQLAdmin](https://github.com/aminalaee/sqladmin) admin panel
- Preview mode to inspect changes before applying them
- Protection for your manual edits in generated files (`USER_MODIFIED` marker)
- Reverse conversion: generated code back to DBML
- Interactive CLI and direct commands

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or any other Python environment manager

## Installation

### Code generation only

```bash
pip install dbml-to-sqlmodel
```

### To run the generated applications

```bash
# Install with runtime dependencies
pip install "dbml-to-sqlmodel[runtime]"

# Or install the runtime dependencies separately in your project
pip install "fastapi[all]" sqlmodel fastcrud sqladmin aiosqlite

# Or, when working inside this repository
uv sync --extra runtime
```

## Quick Start

### 1. Create a DBML schema

Create a `schema.dbml` file describing your database. For example:

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

![DBML schema](https://raw.githubusercontent.com/azhig/dbml-to-sqlmodel/main/docs/img/dbml.png)

### 2. Generate the application

```bash
dbml-to-sqlmodel generate schema.dbml -o output
```

Or launch the interactive mode:

```bash
dbml-to-sqlmodel
# or the alternative command
dbml2sm
```

![Interactive CLI](https://raw.githubusercontent.com/azhig/dbml-to-sqlmodel/main/docs/img/cli.png)

After generation, all SQLModel objects and their `FastCRUD` routers are created
automatically in the target directory.

### 3. Configure the environment

```bash
cd output
echo "DATABASE_URL=sqlite+aiosqlite:///./database.db" > .env

# Install the runtime dependencies if they are not installed yet
pip install "dbml-to-sqlmodel[runtime]"
```

### 4. Run the application

```bash
python main.py

# From this repository you can also run it via Make.
# `make run` first installs the runtime dependencies (uv sync --extra runtime)
# and then starts the server; `make dev` does the same with hot reload.
make run
```

### 5. Open it in the browser

- API documentation: `http://localhost:8001/docs`

![API docs](https://raw.githubusercontent.com/azhig/dbml-to-sqlmodel/main/docs/img/docs.png)

- SQLAdmin panel: `http://localhost:8001/admin`

![Admin panel](https://raw.githubusercontent.com/azhig/dbml-to-sqlmodel/main/docs/img/admin.png)

## Generated Structure

The generator produces a modular project with a dedicated directory per table:

```text
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

For a detailed description of the structure, see the
[CLI Guide](https://github.com/azhig/dbml-to-sqlmodel/blob/main/docs/CLI_GUIDE.md).

## Using It in Your Own Project

`dbml-to-sqlmodel` is a **code generator**: you need it while developing (to scaffold
and regenerate code from your schema), but the running application never imports it.
The recommended setup is therefore:

- add the generator itself as a **development** dependency, and
- add the libraries the generated app uses as your project's **runtime** dependencies.

### 1. Add the generator as a dev dependency

```bash
# uv (recommended)
uv add --dev dbml-to-sqlmodel

# Poetry
poetry add --group dev dbml-to-sqlmodel

# pip (e.g. into requirements-dev.txt)
pip install dbml-to-sqlmodel
```

### 2. Add the runtime libraries the generated app needs

The generated project imports FastAPI, SQLModel, FastCRUD, SQLAdmin and an async
database driver. Add them as regular (runtime) dependencies of your project:

```bash
uv add "fastapi[all]" sqlmodel fastcrud sqladmin aiosqlite greenlet
```

> `greenlet` is required by SQLAlchemy's async engine and is **not** auto-installed
> on every platform/Python combination, so add it explicitly — otherwise the app
> fails to start with `the greenlet library is required`.

### 3. Recommended workflow

1. Keep `schema.dbml` under version control and treat it as the single source of truth.
2. Regenerate the code whenever the schema changes:
   ```bash
   uv run dbml-to-sqlmodel generate schema.dbml -o output
   ```
3. Preview the changes before applying them to an existing project:
   ```bash
   uv run dbml-to-sqlmodel preview schema.dbml -o output
   ```
4. Protect any file you edit by hand with a `# USER_MODIFIED` marker (see
   [Protecting Your Modifications](#protecting-your-modifications)); such files are
   kept on regeneration unless you pass `--force`.
5. If you adjusted the models by hand, you can sync the schema back from the code:
   ```bash
   uv run dbml-to-sqlmodel code-to-dbml output -o schema.dbml
   ```
6. Commit both `schema.dbml` and the generated code so the repository stays reproducible.

## CLI Usage

Full CLI reference: [CLI Guide](https://github.com/azhig/dbml-to-sqlmodel/blob/main/docs/CLI_GUIDE.md).

### Quick Commands

Everywhere `dbml-to-sqlmodel` can be replaced with the shorter `dbml2sm`.

```bash
# Interactive CLI mode
dbml-to-sqlmodel

# Generate the application
dbml-to-sqlmodel generate schema.dbml -o output

# Preview changes
dbml-to-sqlmodel preview schema.dbml

# Schema information
dbml-to-sqlmodel info schema.dbml

# Reverse conversion: code -> DBML
dbml-to-sqlmodel code-to-dbml output -o schema.dbml

# Show the installed version
dbml-to-sqlmodel --version
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=sqlite+aiosqlite:///./database.db
```

### SQLAdmin Authentication

To enable authentication for the admin panel:

```bash
dbml-to-sqlmodel generate schema.dbml --admin-auth
```

Add the following to `.env`:

```env
ADMIN_USER=admin
ADMIN_PASS=your-secure-password
ADMIN_SECRET=your-secret-key-must-be-at-least-32-characters-long
```

![Admin login](https://raw.githubusercontent.com/azhig/dbml-to-sqlmodel/main/docs/img/admin_login.png)

Other configuration options are described in the
[CLI Guide](https://github.com/azhig/dbml-to-sqlmodel/blob/main/docs/CLI_GUIDE.md).

## Protecting Your Modifications

If you edit generated files and want to protect them from being overwritten on
regeneration, add the following comment at the top of the file:

```python
# USER_MODIFIED
```

Files with this marker are not overwritten unless you pass the `--force` flag.

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

## Documentation

- [CLI Guide](https://github.com/azhig/dbml-to-sqlmodel/blob/main/docs/CLI_GUIDE.md) — full command reference and usage examples
- [Changelog](https://github.com/azhig/dbml-to-sqlmodel/blob/main/CHANGELOG.md)
- [Contributing](https://github.com/azhig/dbml-to-sqlmodel/blob/main/CONTRIBUTING.md)

## Contributing

Contributions are welcome! Please read the
[contributing guidelines](https://github.com/azhig/dbml-to-sqlmodel/blob/main/CONTRIBUTING.md)
before opening a pull request.

## License

This project is licensed under the terms of the
[MIT License](https://github.com/azhig/dbml-to-sqlmodel/blob/main/LICENSE).
