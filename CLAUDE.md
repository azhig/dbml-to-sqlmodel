# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a DBML-to-CRUD generator that automatically creates a complete FastAPI application with admin panel from DBML database schema definitions. The tool parses DBML files and generates SQLModel models, FastCRUD routers, and SQLAdmin views.

**Key Features:**
- Bidirectional sync: DBML ⇄ Code
- Patch-based updates: Changes are applied as diffs, preserving formatting
- Interactive CLI with preview and confirmation
- Protection for user-modified files

## Project Structure

```
dbml_to_crud/
├── src/                    # Generator source code
│   ├── dbml_to_sqlmodel.py # DBML parser and SQLModel generator
│   └── generate_app.py     # Main generation script
├── schemas/                # DBML schema files
│   └── schema.dbml         # Example AI Skills schema
├── output/                 # Generated FastAPI application (gitignored)
│   ├── models.py           # SQLModel ORM models
│   ├── crud/               # FastCRUD routers
│   ├── admin.py            # SQLAdmin views
│   ├── main.py             # FastAPI application
│   └── database.db         # SQLite database
├── tests/                  # Unit tests
├── pyproject.toml          # Python dependencies
├── Makefile                # Development commands
└── CLAUDE.md               # This file
```

## Key Commands

### Using Makefile (Recommended)
```bash
make help           # Show all available commands
make install        # Install dependencies
make generate       # Generate FastAPI app from schemas/schema.dbml to output/
make dev            # Run server with hot-reload (port 8001)
make run            # Run server (production mode)
make clean          # Remove output/ directory and cache
make db-reset       # Delete database for schema recreation
make fresh          # Clean + regenerate
make full-reset     # Complete reset: clean, db-reset, generate, run
make format         # Format code with ruff
make lint           # Lint code with ruff
```

### Manual Commands

#### Package Management
```bash
# Install dependencies (using uv package manager)
uv sync

# Activate virtual environment
source .venv/bin/activate
```

#### Generate FastAPI Application
```bash
# Generate complete FastAPI app from DBML schema
uv run python src/generate_app.py schemas/schema.dbml -o output

# Custom output directory
uv run python src/generate_app.py schemas/my_schema.dbml -o my_output

# This creates in output/:
# - models.py (SQLModel models with Create/Update schemas)
# - crud/__init__.py (FastCRUD routers)
# - admin.py (SQLAdmin views)
# - main.py (FastAPI application)
# - requirements.txt (dependencies)
```

#### Run the Generated Application
```bash
# Run the FastAPI server (from output directory)
cd output && uv run python main.py

# Or using uvicorn directly with hot-reload
cd output && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## Architecture

### Code Generation Pipeline

The application uses a two-stage generation process:

1. **DBML Parsing** ([src/dbml_to_sqlmodel.py](src/dbml_to_sqlmodel.py))
   - `parse_dbml()`: Uses PyDBML to parse DBML schema into structured `TableInfo` and `ColumnInfo` dataclasses
   - Extracts tables, columns, relationships (foreign keys), notes, and constraints
   - Processes references bidirectionally to handle both `>` and `<` relationship notations

2. **Code Generation** ([src/generate_app.py](src/generate_app.py))
   - `generate_sqlmodel()`: Creates SQLModel classes with:
     - Main table models (with `table=True`)
     - `Relationship()` fields for foreign keys
     - Create schemas (BaseModel, excludes auto-increment PKs)
     - Update schemas (BaseModel, all fields optional except PKs)
     - Field descriptions from DBML notes
   - `generate_crud_routers()`: Generates FastCRUD routers for each model
   - `generate_admin_views()`: Creates SQLAdmin ModelView classes with automatic icon selection
   - `generate_main_app()`: Creates FastAPI application boilerplate
   - All files are output to the specified directory (default: `output/`)

### Key Design Decisions

**Directory Separation**: Generator code lives in `src/`, schemas in `schemas/`, and generated applications in `output/` (gitignored). This keeps the codebase clean and allows multiple schema files.

**SQLModel Type Mapping**: The generator maps DBML types to Python types via `type_mapping` dict in [src/dbml_to_sqlmodel.py:114-132](src/dbml_to_sqlmodel.py#L114-L132). Serial types become `Optional[int]` with `default=None` for auto-increment behavior.

**Relationships**: Foreign keys are converted to SQLModel `Relationship()` fields. The target table name is singularized by stripping trailing 's'. Nullable foreign keys generate `Optional["TargetClass"]` relationships.

**Schema Separation**: Each table generates three classes:
- `TableName(SQLModel, table=True)` - ORM model
- `TableNameCreate(BaseModel)` - For POST requests (no PK)
- `TableNameUpdate(BaseModel)` - For PATCH requests (all optional)

**Admin Panel Icons**: [src/generate_app.py:43-63](src/generate_app.py#L43-L63) implements automatic icon selection based on table name keywords using Font Awesome icons.

**Database Engine**: Uses SQLite with aiosqlite async driver by default. Connection string in generated `output/main.py`.

### Generated File Structure

After running `make generate`:
```
output/
├── models.py           # SQLModel classes (models + schemas)
├── crud/
│   └── __init__.py     # FastCRUD routers for all models
├── admin.py            # SQLAdmin views configuration
├── main.py             # FastAPI app with DB initialization
├── requirements.txt    # Python dependencies
└── database.db         # SQLite database (created on first run)
```

## Dependencies

Core stack (defined in [pyproject.toml](pyproject.toml)):
- **FastAPI**: Web framework
- **SQLModel**: ORM (combines SQLAlchemy + Pydantic)
- **FastCRUD**: Automatic CRUD router generation
- **SQLAdmin**: Admin panel UI
- **PyDBML**: DBML parser
- **aiosqlite**: Async SQLite driver
- **unidiff**: For patch-based DBML updates

## Code → DBML (Reverse Engineering)

The CLI includes a `Code → DBML` command that reverse-engineers DBML from generated SQLModel code.

### How It Works

1. **Parse Models**: Reads all models from `output/models/` directory
2. **Generate DBML**: Converts SQLModel classes back to DBML format
3. **Show Diff**: Displays unified diff between existing and new DBML
4. **Apply Patch**: Applies changes as a patch, preserving formatting

### Patch Application

Instead of overwriting the entire file, the system:
- Generates a unified diff of changes
- Parses the diff using `unidiff` library
- Applies only the actual changes to the file
- Preserves original formatting, comments, and structure

See [PATCH_APPLICATION.md](PATCH_APPLICATION.md) for technical details.

### Example Workflow

```bash
# 1. Start with DBML schema
dbml-crud  # Select "DBML → Code"

# 2. Manually edit generated models in output/models/
# e.g., rename field: direction_id → direction_id2

# 3. Reverse-engineer back to DBML
dbml-crud  # Select "Code → DBML"

# 4. View diff and apply changes
# Only the renamed field is changed in schema.dbml
```

### Benefits

- ✅ Preserves manual formatting in DBML files
- ✅ Minimal diffs for version control
- ✅ Safe to use with commented DBML
- ✅ Fallback to full rewrite if patch fails

## Important Notes

- The generated code imports `get_session` from `main.py` in `crud/__init__.py`, so main.py must be created first
- All generated SQLModel fields include `description` from DBML column notes for API documentation
- The `schemas/schema.dbml` file is an example schema for an AI Skills Management system
- Primary keys are auto-increment integers by default (serial/serial4 types)
- The admin panel automatically creates plural names by appending 's' to model names
- Generated files in `output/` are gitignored - don't edit them directly, regenerate from DBML instead
- To work with multiple schemas, place them in `schemas/` and specify the path when generating
