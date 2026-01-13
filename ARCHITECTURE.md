# Architecture

## Overview

DBML to CRUD Generator follows a modular architecture with clear separation of concerns. The codebase is organized into specialized packages, each handling a specific aspect of the application.

## Directory Structure

```
src/dbml_to_code/
├── core/                       # Core business logic
│   ├── parser.py              # DBML parsing (PyDBML integration)
│   ├── code_generator.py      # SQLModel code generation
│   └── config.py              # Configuration management
│
├── models/                     # Data models
│   ├── schema.py              # TableInfo, ColumnInfo, RelationshipInfo
│   ├── config_models.py       # AppConfig (Pydantic model)
│   └── file_info.py           # FileStatus, FileInfo
│
├── utils/                      # Utilities
│   ├── file_manager.py        # File I/O, protection, status
│   ├── diff.py                # Diff generation & patching
│   ├── formatters.py          # Rich output formatting
│   └── type_mapping.py        # DBML ↔ Python type conversion
│
├── integrations/              # External library adapters
│   └── pydbml_adapter.py      # PyDBML wrapper utilities
│
├── commands/                   # CLI commands (Typer)
│   ├── generate.py            # Generate FastAPI app
│   ├── preview.py             # Preview changes
│   ├── info.py                # Show file status
│   └── code_to_dbml.py        # Reverse sync
│
├── constants.py               # Project constants
├── cli.py                     # Interactive menu (Questionary)
├── generator.py               # High-level file generation
├── sqlmodel_to_dbml.py        # Reverse: SQLModel → DBML
│
└── templates/                 # (Future) Template generators
    └── __init__.py
```

## Backward Compatibility

The following files provide backward compatibility for existing code:

- `dbml_to_sqlmodel.py` → Re-exports from `core/parser.py` and `core/code_generator.py`
- `config.py` → Re-exports from `core/config.py` and `models/config_models.py`
- `utils.py` → Re-exports from `utils/*` modules

These compatibility wrappers ensure that existing tests and imports continue to work without modification.

## Key Components

### Core Package

**parser.py** - DBML Parsing
- `parse_dbml(dbml_content: str) -> List[TableInfo]` - Main parser
- `parse_dbml_enums(dbml_content: str) -> Dict[str, List[str]]` - Enum extraction
- `extract_dbml_types(dbml_content: str)` - Raw type extraction for round-tripping
- `extract_dbml_defaults(dbml_content: str)` - Default value extraction

**code_generator.py** - SQLModel Generation
- `generate_single_model(table, all_tables, enums)` - Generate SQLModel code for one table
- `to_class_name(name: str)` - Convert snake_case to PascalCase

**config.py** - Configuration
- `ConfigManager` - Manage `.dbml_to_crud` JSON config file
- Methods: `load()`, `save()`, `update()`, `reset()`

### Models Package

**schema.py** - Schema Models
- `TableInfo` - Table metadata (columns, relationships, notes)
- `ColumnInfo` - Column metadata (type, constraints, references)
- `RelationshipInfo` - Foreign key relationship info

**config_models.py** - Configuration
- `AppConfig` - Pydantic model for app configuration

**file_info.py** - File Status
- `FileStatus` - Enum: created, modified, unchanged, protected
- `FileInfo` - File metadata with status

### Utils Package

**file_manager.py** - File Operations
- `is_user_modified(file_path)` - Check for USER_MODIFIED marker
- `mark_as_user_modified(file_path)` - Add protection marker
- `calculate_file_status(output_dir, generated_files)` - Compute file statuses

**diff.py** - Diff & Patching
- `normalize_model_code(text)` - AST-based normalization
- `generate_diff(original, modified, filename)` - Unified diff
- `apply_diff_to_file(file_path, original, modified)` - Smart patching
- `print_diff(diff_text, filename)` - Rich colorized output

**formatters.py** - Output Formatting
- `print_file_status_table(files_status)` - Rich table for file status

**type_mapping.py** - Type Conversion
- `TYPE_MAPPING` - Dict of DBML → Python types
- `get_python_type(dbml_type)` - Get Python type for DBML type
- `is_auto_increment_type(dbml_type)` - Check if type is serial

### Integrations Package

**pydbml_adapter.py** - PyDBML Utilities
- `setdefaultattr(obj, name, value)` - Helper for dynamic attributes

### Commands Package

Each command is a Typer command function:
- **generate.py** - Generate FastAPI application
- **preview.py** - Show diff without writing
- **info.py** - Display file status report
- **code_to_dbml.py** - Sync changes back to DBML

## Data Flow

### Generation Pipeline

```
DBML File
    ↓
parse_dbml() [core/parser.py]
    ↓
List[TableInfo] + Enums
    ↓
generate_single_model() [core/code_generator.py]
    ↓
Generated Python Code (models, CRUD, admin)
    ↓
calculate_file_status() [utils/file_manager.py]
    ↓
Write Files (respecting USER_MODIFIED)
```

### Reverse Sync Pipeline

```
SQLModel Files
    ↓
sqlmodel_to_dbml.py (AST parsing)
    ↓
DBML Updates
    ↓
Merge with Original DBML
```

## Design Patterns

### 1. Parser-Generator Pattern
- **Parser** (`core/parser.py`) - Converts DBML → internal models
- **Generator** (`core/code_generator.py`) - Converts internal models → Python code
- Separation allows for multiple output formats in the future

### 2. Adapter Pattern
- `integrations/` package wraps external libraries (PyDBML)
- Isolates dependencies, makes them swappable

### 3. Strategy Pattern
- Type mapping is configurable via `utils/type_mapping.py`
- Easy to extend with new type mappings

### 4. Facade Pattern
- `generator.py` provides high-level `generate_all_files()` API
- Hides complexity of orchestrating parser + code generator + file writing

### 5. Factory Pattern
- CRUD routers created via factory functions: `create_{table}_router()`
- Allows dependency injection at runtime

## Future Extensions

### Templates Package (Planned)
The `templates/` directory is reserved for future template-based generation:

```
templates/
├── model_template.py      # SQLModel model generation
├── crud_template.py       # FastCRUD router generation
├── admin_template.py      # SQLAdmin view generation
├── main_template.py       # main.py generation
└── enums_template.py      # Enum generation
```

This would allow:
- Customizable code templates (Jinja2, Mako, etc.)
- Multiple output frameworks (GraphQL, async CRUD, etc.)
- User-provided templates

### Additional Generators
- GraphQL schema generator
- TypeScript type definitions
- Prisma schema converter
- OpenAPI/Swagger specs

## Testing Strategy

- **Unit Tests** - Test individual functions in isolation
  - `tests/test_parser.py` - DBML parsing
  - `tests/test_generator.py` - Code generation

- **Integration Tests** - Test full generation pipeline
  - Generate from sample DBML
  - Verify output file structure
  - Check round-trip (DBML → Code → DBML)

## Migration Notes

### From Old Structure

Old imports are supported via compatibility wrappers:

```python
# Old (still works)
from dbml_to_code.dbml_to_sqlmodel import parse_dbml

# New (recommended)
from dbml_to_code.core import parse_dbml
```

Compatibility files:
- `dbml_to_sqlmodel.py` → `dbml_to_sqlmodel_compat.py`
- `config.py` → `config_compat.py`
- `utils.py` → `utils_compat.py`

Original files are backed up in `.old_structure/`.

### Gradual Migration Path

1. Update imports in new code to use new structure
2. Existing code continues to work with compatibility wrappers
3. Eventually remove compatibility wrappers (breaking change)
4. Update all code to new imports

## Performance Considerations

- **AST Normalization** - Uses Python's `ast` module for accurate code comparison
- **Lazy Loading** - Config loaded on first access
- **Caching** - DBML parsing happens once per generation
- **Streaming** - Large files processed line-by-line where possible

## Security

- **File Protection** - USER_MODIFIED marker prevents accidental overwrites
- **Path Validation** - All file paths validated before write
- **No Eval** - No dynamic code execution (uses AST parsing, not `eval`)
- **Sandboxed Generation** - Generated code written to isolated `output/` directory
