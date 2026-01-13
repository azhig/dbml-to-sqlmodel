# DBML to Code Generator

Generate a complete FastAPI application (SQLModel + FastCRUD + SQLAdmin) from your DBML database schema.

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
pip install dbml-to-code
```

### For Running Generated Applications

```bash
# Install with runtime dependencies
pip install dbml-to-code[runtime]

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
dbml-to-code generate schema.dbml -o output
```

### 3. Setup environment

```bash
cd output
echo "DATABASE_URL=sqlite+aiosqlite:///./database.db" > .env

# Install runtime dependencies if not already installed
pip install dbml-to-code[runtime]
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
# Interactive mode
dbml-to-code

# Generate application
dbml-to-code generate schema.dbml -o output

# Preview changes
dbml-to-code preview schema.dbml

# Show schema info
dbml-to-code info schema.dbml

# Reverse: code to DBML
dbml-to-code code-to-dbml output -o schema.dbml
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
dbml-to-code generate schema.dbml --admin-auth
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
