# Contributing to DBML to SQLModel

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd dbml_to_crud
   ```

2. **Install uv** (if not already installed)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   make install
   # or
   uv sync
   ```

4. **Install pre-commit hooks** (REQUIRED)
   ```bash
   make pre-commit-install
   # or
   uv run pre-commit install
   ```

   This ensures code is automatically formatted and checked before each commit.

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make coverage

# Generate HTML coverage report
make coverage-html
```

### Code Quality

**Before committing, code is automatically formatted:**

Pre-commit hooks will automatically:
- Sort and organize imports
- Format code with Ruff
- Fix linting issues
- Check types with MyPy

**Manual commands:**

```bash
# Format code (includes import sorting)
make format

# Sort imports only
make format-imports

# Lint code
make lint

# Auto-fix linting issues
make lint-fix

# Type checking
make typecheck

# Run ALL checks at once (recommended before PR)
make check

# Run all pre-commit hooks manually
make pre-commit
```

### Testing Your Changes

```bash
# Generate app from example schema
make generate

# Preview changes without writing
make preview

# Run development server
make dev
```

## Code Style

This project uses:
- **Ruff** for linting, formatting, and import sorting
- **MyPy** for type checking
- **Pre-commit hooks** for automatic code quality checks

### Import Organization

Imports are automatically sorted on commit using Ruff's isort implementation:
- Standard library imports first
- Third-party imports second
- Local imports last
- Alphabetically sorted within each group

### Type Hints

- Type hints encouraged for public APIs
- Use `typing` module for complex types
- MyPy checks enabled but not strict mode

### Code Formatting

- Line length: 100 characters
- Use double quotes for strings
- Follow PEP 8 conventions

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(parser): add support for composite primary keys
fix(generator): handle nullable foreign keys correctly
docs(readme): update installation instructions
```

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write tests for new features
   - Update documentation if needed
   - Ensure all tests pass
   - Run code quality checks

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Ensure CI checks pass

## Project Structure

```
dbml_to_crud/
├── src/
│   └── dbml_to_sqlmodel/     # Main package
│       ├── cli.py            # CLI entry point
│       ├── parser.py         # DBML parser
│       ├── generator.py      # Code generator
│       ├── config.py         # Configuration
│       └── templates/        # Jinja2 templates
├── tests/                    # Test files
├── examples/                 # Example schemas
├── Makefile                  # Development commands
└── pyproject.toml           # Project metadata
```

## Adding New Features

### 1. Parser Changes

If adding new DBML features:
- Update `parser.py`
- Add tests in `tests/test_parser.py`
- Update schema models if needed

### 2. Code Generation

If changing generated code:
- Modify templates in `src/dbml_to_sqlmodel/templates/`
- Update `generator.py` if needed
- Add tests in `tests/test_generator.py`
- Verify with `make generate`

### 3. CLI Commands

If adding new commands:
- Update `cli.py`
- Add command to Makefile
- Update CLI_GUIDE.md
- Add tests

## Testing Guidelines

- Write tests for all new features
- Aim for >80% code coverage
- Use descriptive test names
- Test edge cases and error conditions

Example test structure:
```python
def test_feature_name():
    """Test description."""
    # Arrange
    input_data = ...

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

## Documentation

- Update README.md for user-facing changes
- Update CLI_GUIDE.md for CLI changes
- Add docstrings to all public functions
- Update CHANGELOG.md with your changes

## Questions?

Feel free to open an issue for:
- Bug reports
- Feature requests
- Questions about contributing
- Suggestions for improvement

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help maintain a positive community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
