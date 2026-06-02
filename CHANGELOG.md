# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-02

Initial public release.

### Added

- DBML to SQLModel model generation
- FastAPI CRUD endpoint generation powered by
  [FastCRUD](https://github.com/igorbenav/fastcrud)
- Optional [SQLAdmin](https://github.com/aminalaee/sqladmin) admin panel, with
  optional constant-time credential authentication (`--admin-auth`)
- Modular generated project: one package per table, plus a wired-up `main.py`
  that uses the FastAPI `lifespan` API and reads `DATABASE_URL` from the
  environment (`.env`)
- Correct temporal type mapping: DBML `timestamp`/`datetime`/`date`/`time` map to
  Python `datetime`/`date`/`time` with the matching imports
- PascalCase class names and singularized relationship attribute names
- Interactive CLI (`questionary`) plus direct subcommands: `generate`,
  `preview`, `info` and `code-to-dbml`
- Preview mode with diff display and protection for manual edits via the
  `USER_MODIFIED` marker
- Reverse conversion: generated code back to DBML
- `--version` / `-V` flag
- Generated `requirements.txt` with runtime versions aligned to the tested
  stack (including `greenlet`, which the async SQLAlchemy engine needs but
  which is not auto-installed on every platform)
- `py.typed` marker (PEP 561) and full PyPI packaging metadata (authors,
  keywords, Trove classifiers, project URLs)
- Documentation: README, CLI guide and contributing guidelines
- Tooling: Ruff, MyPy, pre-commit, Dependabot, GitHub Actions CI with Codecov
  coverage and a PyPI trusted-publishing workflow
- Test suite with 100% coverage, including smoke tests that compile the
  generated application and guard temporal-type, lifespan and requirements
  regressions

[0.1.0]: https://github.com/azhig/dbml-to-sqlmodel/releases/tag/v0.1.0
