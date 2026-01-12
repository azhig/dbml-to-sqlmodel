# Repository Guidelines

## Project Structure & Module Organization
- `src/dbml_to_crud/` contains the CLI entrypoint, parsing, and generation logic.
- `src/dbml_to_crud/commands/` holds CLI subcommands (generate, preview, info, code_to_dbml).
- `schemas/` stores DBML inputs (for example `schemas/schema.dbml`).
- `output/` is generated FastAPI code (models, routers, admin, `main.py`). Treat it as disposable.
- `tests/` contains pytest tests (currently `tests/test_parser.py`).
- `Makefile` and `README.md` document common workflows and CLI usage.

## Build, Test, and Development Commands
Prefer Makefile targets for consistent tooling.
- `make install` — sync dependencies via `uv`.
- `make cli` — launch the interactive CLI (`uv run dbml-crud`).
- `make generate` — generate app from `schemas/schema.dbml` into `output/`.
- `make preview` — show diffs for `models/*/model.py` without writing files.
- `make info` — report generated files and mismatches vs current output.
- `make dev` — run the generated app with reload on port 8001.
- `make test` — run pytest.
- `make format` / `make lint` — run `ruff` formatter and linter.

You can also call the CLI directly, e.g. `uv run dbml-crud generate schemas/schema.dbml -o output`.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, UTF-8 source.
- Format and lint with `ruff` (`make format`, `make lint`).
- Use `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep CLI behavior in `src/dbml_to_crud/commands/` and shared utilities in `src/dbml_to_crud/utils.py`.

## Testing Guidelines
- Framework: `pytest`.
- Place tests under `tests/` with `test_*.py` naming.
- Example: `uv run pytest tests/test_parser.py -v`.

## Commit & Pull Request Guidelines
- This repo has no commit history yet, so no established convention.
- Use clear, imperative commit messages (e.g., "Fix DBML type normalization").
- PRs should include: purpose, how to test (exact commands), and screenshots for CLI output changes.

## Generation Notes
- Generated files can be protected with a `# USER_MODIFIED` marker; generation skips them unless forced.
- Default output path is `output/`; pass `-o` to change it.
