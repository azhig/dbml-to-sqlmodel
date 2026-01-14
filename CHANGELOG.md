# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Ruff configuration for linting and formatting
- Pre-commit hooks for code quality
- MyPy type checking support
- Dependabot for automated dependency updates
- CHANGELOG.md for tracking version changes
- CONTRIBUTING.md guidelines

### Changed
- Project structure refactored from `dbml_to_code` to `dbml_to_sqlmodel`
- Updated Makefile with correct CLI commands
- Improved .gitignore patterns

## [0.1.0] - 2026-01-14

### Added
- Initial release
- DBML to SQLModel conversion
- FastAPI CRUD generation
- Interactive CLI with questionary
- Preview mode with diff display
- Info command for file inspection
- GitHub Actions CI/CD pipeline
- Test coverage reporting
- Example schema files

### Features
- Generate SQLModel models from DBML schemas
- Auto-generate FastAPI CRUD endpoints
- SQLAdmin integration
- Database migrations support
- Type-safe code generation
- CLI with multiple commands (generate, preview, info)

[Unreleased]: https://github.com/yourusername/dbml-to-sqlmodel/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/dbml-to-sqlmodel/releases/tag/v0.1.0
