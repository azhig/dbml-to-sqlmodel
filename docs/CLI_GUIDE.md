# CLI Usage Guide

Complete guide for using the `dbml-to-sqlmodel` command-line interface.

## Table of Contents

- [Installation](#installation)
- [Interactive Mode](#interactive-mode)
- [Commands](#commands)
  - [generate](#generate)
  - [preview](#preview)
  - [info](#info)
  - [code-to-dbml](#code-to-dbml)
- [Configuration](#configuration)
- [File Protection](#file-protection)
- [Examples](#examples)

## Installation

### For Code Generation Only

Install just the generator tool (lightweight, no runtime dependencies):

```bash
pip install dbml-to-sqlmodel
```

### For Running Generated Applications

If you want to run the generated application, install with runtime dependencies:

```bash
pip install dbml-to-sqlmodel[runtime]
```

Or install runtime dependencies separately in your project:

```bash
pip install fastapi[all] sqlmodel fastcrud sqladmin aiosqlite
```

## Interactive Mode

Launch the interactive CLI menu:

```bash
dbml-to-sqlmodel
```

Interactive mode provides a guided experience:

1. **Select DBML file** - Browse and select your schema file
2. **Choose output directory** - Specify where to generate files
3. **Configure options** - Set generation parameters
4. **Preview mode** - Review changes before applying
5. **Save settings** - Store configuration for future use

The interactive mode saves your preferences to `.dbml_to_code` in the project directory.

## Commands

### generate

Generate a complete FastAPI application from DBML schema.

**Syntax:**

```bash
dbml-to-sqlmodel generate <schema_file> [OPTIONS]
```

**Arguments:**

- `schema_file` - Path to DBML schema file (required)

**Options:**

- `-o, --output <dir>` - Output directory (default: `output`)
- `--admin-auth` - Enable authentication in SQLAdmin panel
- `--force` - Overwrite files marked as USER_MODIFIED
- `--help` - Show help message

**Examples:**

```bash
# Basic generation
dbml-to-sqlmodel generate examples/schema.dbml

# Custom output directory
dbml-to-sqlmodel generate examples/schema.dbml -o my_app

# With admin authentication
dbml-to-sqlmodel generate examples/schema.dbml --admin-auth

# Force overwrite protected files
dbml-to-sqlmodel generate examples/schema.dbml --force
```

**Generated Structure:**

```
output/
├── main.py              # FastAPI application
├── admin.py             # SQLAdmin configuration
├── requirements.txt     # Project dependencies
└── models/
    ├── __init__.py      # Root init (imports all models)
    ├── enums.py         # (Optional) DBML enums
    ├── users/
    │   ├── __init__.py  # Local init (exports models and router)
    │   ├── model.py     # SQLModel classes (Base, Main, Create, Update)
    │   └── crud.py      # FastCRUD router
    ├── posts/
    │   ├── __init__.py
    │   ├── model.py
    │   └── crud.py
    └── ... (one directory per table)
```

### preview

Preview changes without applying them. Shows which files will be created, modified, or skipped.

**Syntax:**

```bash
dbml-to-sqlmodel preview <schema_file> [OPTIONS]
```

**Arguments:**

- `schema_file` - Path to DBML schema file (required)

**Options:**

- `-o, --output <dir>` - Output directory (default: `output`)
- `--help` - Show help message

**Output:**

The preview shows a table with file statuses:

- `CREATE` - New file will be created
- `UPDATE` - Existing file will be modified
- `SKIP` - File is protected (USER_MODIFIED marker)
- `UNCHANGED` - File content is identical

**Examples:**

```bash
# Preview changes
dbml-to-sqlmodel preview examples/schema.dbml

# Preview with custom output directory
dbml-to-sqlmodel preview examples/schema.dbml -o my_app

# Preview, then generate
dbml-to-sqlmodel preview examples/schema.dbml && dbml-to-sqlmodel generate schema.dbml
```

### info

Display schema information: tables, columns, types, and relationships.

**Syntax:**

```bash
dbml-to-sqlmodel info <schema_file>
```

**Arguments:**

- `schema_file` - Path to DBML schema file (required)

**Output:**

Shows:
- Table names and column counts
- Column details (name, type, constraints)
- Relationships between tables
- Primary keys and foreign keys

**Example:**

```bash
dbml-to-sqlmodel info examples/schema.dbml
```

**Sample Output:**

```
Schema: schema.dbml

Table: users (4 columns)
├── id: int [PK]
├── username: str [unique, not null]
├── email: str [unique, not null]
└── created_at: datetime

Table: posts (5 columns)
├── id: int [PK]
├── title: str [not null]
├── content: str
├── user_id: int [FK -> users.id]
└── created_at: datetime

Relationships:
  posts.user_id -> users.id (Many-to-One)
```

### code-to-dbml

Reverse conversion: generate DBML schema from existing generated code.

**Syntax:**

```bash
dbml-to-sqlmodel code-to-dbml <source_dir> [OPTIONS]
```

**Arguments:**

- `source_dir` - Directory with generated code (required)

**Options:**

- `-o, --output <file>` - Output DBML file (default: `schema.dbml`)
- `--help` - Show help message

**Examples:**

```bash
# Generate DBML from code
dbml-to-sqlmodel code-to-dbml output

# Custom output file
dbml-to-sqlmodel code-to-dbml output -o new_schema.dbml

# Update existing schema
dbml-to-sqlmodel code-to-dbml my_app -o examples/schema.dbml
```

**Use Cases:**

1. Document existing generated code
2. Sync DBML after manual code changes
3. Create backup of current schema state
4. Compare schemas across versions

## Generated Project Structure

### Overview

The generator creates a modular structure where each table gets its own directory with model and CRUD files:

```
output/
├── main.py                          # FastAPI application entry point
├── admin.py                         # SQLAdmin panel configuration
├── requirements.txt                 # Project dependencies
├── .env                            # Environment variables (created manually)
└── models/
    ├── __init__.py                 # Exports all models and routers
    ├── enums.py                    # (Optional) DBML enum definitions
    │
    ├── users/                      # Table: users
    │   ├── __init__.py            # Exports Users, UsersCreate, UsersUpdate, create_users_router
    │   ├── model.py               # SQLModel classes
    │   └── crud.py                # FastCRUD router factory
    │
    ├── posts/                      # Table: posts
    │   ├── __init__.py
    │   ├── model.py
    │   └── crud.py
    │
    └── categories/                 # Table: categories
        ├── __init__.py
        ├── model.py
        └── crud.py
```

### File Details

#### `models/{table}/model.py`

Contains 4 SQLModel classes for each table:

```python
# Example: models/users/model.py

from sqlmodel import SQLModel, Field
from typing import Optional

# 1. Base class - shared fields (no PK)
class UsersBase(SQLModel):
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    full_name: Optional[str] = None

# 2. Main table class - with PK and relationships
class Users(UsersBase, table=True):
    """Users table"""
    id: Optional[int] = Field(default=None, primary_key=True)

# 3. Create schema - for POST requests (no PK)
class UsersCreate(UsersBase):
    """Create schema for users"""
    pass

# 4. Update schema - for PATCH requests (all Optional)
class UsersUpdate(SQLModel):
    """Update schema for users"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
```

#### `models/{table}/crud.py`

Contains router factory function:

```python
# Example: models/users/crud.py

from fastcrud import crud_router
from .model import Users, UsersCreate, UsersUpdate

def create_users_router(get_session):
    """Create CRUD router with session dependency"""
    return crud_router(
        model=Users,
        create_schema=UsersCreate,
        update_schema=UsersUpdate,
        path='/users',
        tags=['users'],
        session=get_session
    )
```

#### `models/{table}/__init__.py`

Exports classes and router:

```python
# Example: models/users/__init__.py

from .model import Users, UsersCreate, UsersUpdate
from .crud import create_users_router

__all__ = [
    "Users",
    "UsersCreate",
    "UsersUpdate",
    "create_users_router",
]
```

#### `models/__init__.py`

Root init that exports everything:

```python
# models/__init__.py

from .users import Users, UsersCreate, UsersUpdate, create_users_router
from .posts import Posts, PostsCreate, PostsUpdate, create_posts_router
from .categories import Categories, CategoriesCreate, CategoriesUpdate, create_categories_router

__all__ = [
    # Users
    "Users", "UsersCreate", "UsersUpdate", "create_users_router",
    # Posts
    "Posts", "PostsCreate", "PostsUpdate", "create_posts_router",
    # Categories
    "Categories", "CategoriesCreate", "CategoriesUpdate", "create_categories_router",
]
```

#### `models/enums.py`

Generated only if DBML contains enum definitions:

```python
# models/enums.py

from enum import Enum

class StatusEnum(str, Enum):
    """DBML enum: status"""
    __dbml_name__ = "status"
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
```

#### `main.py`

FastAPI application entry point:

```python
# main.py (simplified)

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

# Import router factories
from models.users import create_users_router
from models.posts import create_posts_router

app = FastAPI(title="Generated API")

# Database setup
engine = create_async_engine("sqlite+aiosqlite:///./database.db")

# Create session dependency
async def get_session():
    async with AsyncSession(engine) as session:
        yield session

# Initialize routers
users_router = create_users_router(get_session)
posts_router = create_posts_router(get_session)

# Register routers
app.include_router(users_router)
app.include_router(posts_router)

# Initialize admin panel
from admin import init_admin
init_admin(app, engine)
```

#### `admin.py`

SQLAdmin panel configuration:

```python
# admin.py (simplified)

from sqladmin import Admin, ModelView
from models.users import Users
from models.posts import Posts

def init_admin(app, engine):
    admin = Admin(app, engine)

    class UsersAdmin(ModelView, model=Users):
        name = "User"
        name_plural = "Users"
        icon = "fa-solid fa-user"

    class PostsAdmin(ModelView, model=Posts):
        name = "Post"
        name_plural = "Posts"
        icon = "fa-solid fa-file-text"

    admin.add_view(UsersAdmin)
    admin.add_view(PostsAdmin)

    return admin
```

#### `requirements.txt`

Project dependencies:

```txt
fastapi>=0.104.0
sqlmodel>=0.0.14
sqladmin>=0.22.0
fastcrud>=0.20.1
uvicorn[standard]>=0.23.0
aiosqlite>=0.19.0
python-dotenv>=1.0.0
```

### Import Patterns

**Import a model:**
```python
from models.users import Users, UsersCreate, UsersUpdate
```

**Import multiple models:**
```python
from models.users import Users
from models.posts import Posts
from models.categories import Categories
```

**Import from root (if needed):**
```python
from models import Users, Posts, Categories
```

### Benefits of This Structure

1. **Modularity** - Each table is self-contained in its directory
2. **Scalability** - Easy to find files even with 50+ tables
3. **Extensibility** - Add custom files to table directories:
   ```
   users/
   ├── model.py
   ├── crud.py
   ├── schemas.py      # Custom Pydantic schemas
   ├── services.py     # Business logic
   └── validators.py   # Custom validators
   ```
4. **Isolation** - Changes to one table don't affect others
5. **Microservices Ready** - Easy to extract a table module into separate service

## Configuration

### Settings File

CLI saves configuration to `.dbml_to_code` in your project directory.

**Format:**

```json
{
  "schema_file": "schema.dbml",
  "output_dir": "output",
  "preview_enabled": true,
  "overwrite": false,
  "admin_auth": false
}
```

**Parameters:**

- `schema_file` - Default DBML file path
- `output_dir` - Default output directory
- `preview_enabled` - Show preview before generation
- `overwrite` - Overwrite USER_MODIFIED files
- `admin_auth` - Enable admin authentication

### Environment Variables

For generated applications, create `.env` file:

**Basic Configuration:**

```env
DATABASE_URL=sqlite+aiosqlite:///./database.db
```

**With Admin Authentication:**

```env
DATABASE_URL=sqlite+aiosqlite:///./database.db
ADMIN_USER=admin
ADMIN_PASS=your-secure-password
ADMIN_SECRET=your-secret-key-must-be-at-least-32-characters-long
```

**Security Notes:**

- Never commit `.env` to version control
- Use strong passwords in production
- Keep `ADMIN_SECRET` at least 32 characters
- Rotate secrets regularly

## File Protection

### Protecting Your Modifications

Add a marker to prevent file overwriting:

```python
# USER_MODIFIED

# Your custom code here
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    # Your custom fields...
```

**Behavior:**

- Files with `# USER_MODIFIED` are skipped during regeneration
- Use `--force` flag to override protection
- Preview mode shows protected files as `SKIP`

### Force Overwrite

Override file protection:

```bash
dbml-to-sqlmodel generate schema.dbml --force
```

**Warning:** This will overwrite ALL files, including USER_MODIFIED ones.

## Examples

### Complete Workflow

```bash
# 1. Create schema
cat > schema.dbml <<EOF
Table users {
  id integer [primary key]
  username varchar(255) [unique, not null]
  email varchar(255) [unique, not null]
}
EOF

# 2. Inspect schema
dbml-to-sqlmodel info schema.dbml

# 3. Preview generation
dbml-to-sqlmodel preview schema.dbml

# 4. Generate application
dbml-to-sqlmodel generate schema.dbml

# 5. Setup environment
cd output
echo "DATABASE_URL=sqlite+aiosqlite:///./database.db" > .env

# 6. Install runtime dependencies (if not installed)
pip install dbml-to-sqlmodel[runtime]

# 7. Run application
python main.py
```

### Update Existing Application

```bash
# 1. Modify schema.dbml (add new table/column)

# 2. Preview changes
dbml-to-sqlmodel preview schema.dbml -o my_app

# 3. Review what will be updated
# Protected files (USER_MODIFIED) won't be touched

# 4. Apply changes
dbml-to-sqlmodel generate schema.dbml -o my_app

# 5. Restart application
cd my_app && python main.py
```

### Multi-Environment Setup

```bash
# Development
dbml-to-sqlmodel generate schema.dbml -o dev_app
cd dev_app
echo "DATABASE_URL=sqlite+aiosqlite:///./dev.db" > .env

# Production
dbml-to-sqlmodel generate schema.dbml -o prod_app --admin-auth
cd prod_app
cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/prod_db
ADMIN_USER=admin
ADMIN_PASS=$(openssl rand -base64 32)
ADMIN_SECRET=$(openssl rand -base64 32)
EOF
```

### Backup and Restore Schema

```bash
# Backup current schema
dbml-to-sqlmodel code-to-dbml output -o backup_$(date +%Y%m%d).dbml

# Restore from backup
dbml-to-sqlmodel generate backup_20260113.dbml -o restored_app
```

## Troubleshooting

### Common Issues

**Issue: `dbml-to-sqlmodel: command not found`**

Solution: Ensure the package is installed and in your PATH:

```bash
pip install --user dbml-to-sqlmodel
# or
pipx install dbml-to-sqlmodel
```

**Issue: Import errors when running generated code**

Solution: Install runtime dependencies:

```bash
pip install dbml-to-sqlmodel[runtime]
```

**Issue: Files not updating**

Solution: Check for USER_MODIFIED markers. Use preview mode:

```bash
dbml-to-sqlmodel preview schema.dbml
```

**Issue: Admin authentication not working**

Solution: Verify `.env` file has correct format and ADMIN_SECRET is ≥32 chars:

```bash
cat .env
# Should contain all three variables
```

## Getting Help

```bash
# General help
dbml-to-sqlmodel --help

# Command-specific help
dbml-to-sqlmodel generate --help
dbml-to-sqlmodel preview --help
dbml-to-sqlmodel info --help
dbml-to-sqlmodel code-to-dbml --help
```

## Related Documentation

- [Main README](README.md) - Quick start and overview
- [DBML Syntax](https://www.dbml.org/docs/) - DBML language reference
- [FastAPI Docs](https://fastapi.tiangolo.com/) - FastAPI framework
- [SQLModel Docs](https://sqlmodel.tiangolo.com/) - SQLModel ORM
