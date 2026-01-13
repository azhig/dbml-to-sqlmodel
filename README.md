# DBML to Code Generator

Generate a FastAPI application (SQLModel + FastCRUD + SQLAdmin) from a DBML schema.

## Features

- Generates models, CRUD routers, and a FastAPI app from DBML
- Optional SQLAdmin panel generation
- Preview and report modes to review changes
- Simple CLI and interactive menu

## Requirements

- Python 3.11+
- uv (recommended) or any Python environment manager

## Installation

Use the Makefile for consistent setup:

```bash
make install
```

## Quick start

1. Put your DBML schema in `examples/schema.dbml` (or update the path in settings).
2. Generate the app:

```bash
make generate
```

3. Run the generated app:

```bash
cd output
uv run python main.py
```

4. Open the admin panel:

```
http://localhost:8001/admin
```

## CLI usage

Interactive mode:

```bash
make cli
```

Direct commands:

```bash
uv run dbml-code generate examples/schema.dbml -o output
uv run dbml-code preview examples/schema.dbml -o output
uv run dbml-code info examples/schema.dbml -o output
uv run dbml-code code-to-dbml examples/schema.dbml -o output
```

## SQLAdmin authentication (optional)

By default, the admin panel is open. You can enable login in the CLI settings or via:

```bash
uv run dbml-code generate examples/schema.dbml -o output --admin-auth
```

Set credentials in a `.env` file next to `output/main.py`:

```env
ADMIN_USER=admin
ADMIN_PASS=change-me
ADMIN_SECRET=replace-this
```

## Configuration

The interactive CLI stores settings in `.dbml_to_code` in the project root. You can update:

- schema file path
- output directory
- preview defaults
- overwrite behavior
- admin auth toggle

## Notes

- `output/` is generated code and can be regenerated at any time.
- Files with `# USER_MODIFIED` are protected unless `--force` is used.

## Development

Common commands:

```bash
make format
make lint
make test
```

## Architecture

The project uses a modular architecture with clear separation of concerns:

- **core/** - Business logic (parsing, code generation, config)
- **models/** - Data structures (TableInfo, ColumnInfo, AppConfig)
- **utils/** - Utilities (file operations, diff, formatters, type mapping)
- **integrations/** - External library adapters (PyDBML)
- **commands/** - CLI commands (generate, preview, info, code-to-dbml)

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation.
