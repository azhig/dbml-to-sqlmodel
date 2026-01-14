# Development Guide

Quick reference for developers working on this project.

## Setup

```bash
# Install dependencies
make install

# Install pre-commit hooks (recommended)
make pre-commit-install
```

## Code Quality

```bash
# Sort and organize imports only
make format-imports

# Format code (includes import sorting)
make format

# Lint code
make lint

# Auto-fix linting issues
make lint-fix

# Type checking
make typecheck

# Run ALL checks at once (format + lint + typecheck + test)
make check

# Run all pre-commit hooks manually
make pre-commit
```

**Recommended workflow before committing:**

```bash
# Quick: format and check everything
make check

# Or run pre-commit hooks (what runs on git commit)
make pre-commit
```

## Testing

```bash
# Run tests
make test

# Run tests with coverage
make coverage

# Generate HTML coverage report
make coverage-html
```

## Project Commands

```bash
# Show all available commands
make help

# Generate app from schema
make generate

# Preview changes without writing
make preview

# Show file information
make info

# Run development server
make dev
```

## Pre-commit Hooks

Hooks run **automatically** on `git commit` and will:
1. **Sort imports** (isort via ruff)
2. **Auto-fix** linting issues
3. **Format code** with ruff
4. **Check types** with mypy
5. Clean up whitespace, EOF, validate YAML/TOML

To run manually before committing:

```bash
make pre-commit
```

**What happens on commit:**
```bash
git add .
git commit -m "feat: your changes"
# → Pre-commit hooks run automatically
# → Code is formatted and fixed
# → If issues found, commit is blocked
# → Fix issues and commit again
```

All hooks include:
- **Import sorting** (ruff --select I)
- **Auto-fixing** linting issues
- **Code formatting** (ruff format)
- Trailing whitespace removal
- EOF fixer
- YAML/TOML validation
- MyPy type checking (excluding tests)

## Configuration Files

- `pyproject.toml` - Project metadata, dependencies, tool configs
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `Makefile` - Development commands
- `.gitignore` - Git ignore patterns

## Code Style

- **Line length**: 100 characters
- **Quotes**: Double quotes
- **Type hints**: Encouraged but not required
- **Docstrings**: Google style

## Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature

# Make changes, commit
git add .
git commit -m "feat: your feature description"

# Push and create PR
git push origin feature/your-feature
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code formatting
- `refactor:` - Code refactoring
- `test:` - Test updates
- `chore:` - Maintenance tasks

## Troubleshooting

### Pre-commit hooks fail

```bash
# Fix automatically where possible
make lint-fix
make format

# Run hooks manually to see errors
make pre-commit
```

### Tests fail

```bash
# Run specific test
uv run pytest tests/test_parser.py -v

# Run with verbose output
uv run pytest tests/ -vv

# Run with pdb on failure
uv run pytest tests/ --pdb
```

### MyPy errors

Check `pyproject.toml` for ignored modules. Add type hints or ignore specific errors:

```python
# type: ignore[error-code]
```

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [MyPy Documentation](https://mypy.readthedocs.io/)
- [Pre-commit Documentation](https://pre-commit.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
