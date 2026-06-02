"""DBML parsing functionality."""

import re
import warnings
from collections.abc import Iterator
from typing import Any

from ..models.schema import ColumnInfo, RelationshipInfo, TableInfo

# Suppress pyparsing deprecation warnings from pydbml library
# pydbml uses old pyparsing API (camelCase) which triggers deprecation warnings
# in pyparsing 3.3+. These warnings occur during module import when pydbml
# defines its parser grammar. This is a known issue in pydbml that cannot be
# fixed without updating the pydbml library itself.
# See: https://pyparsing-docs.readthedocs.io/en/latest/whats_new_in_3_0_0.html
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    from pydbml import PyDBML as _PyDBML


def PyDBML(content: str) -> Any:
    """Wrapper around PyDBML to suppress pyparsing deprecation warnings.

    Args:
        content: DBML schema content to parse

    Returns:
        Parsed DBML database object
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        return _PyDBML(content)


def parse_dbml(dbml_content: str) -> list[TableInfo]:
    """Parse DBML content using PyDBML into structured table definitions."""
    raw_types = extract_dbml_types(dbml_content)
    raw_defaults = extract_dbml_defaults(dbml_content)
    parsed = PyDBML(dbml_content)
    tables = []

    # Map each source column to the foreign-key refs that originate from it,
    # keyed by object identity so the PyDBML objects are never mutated.
    column_refs: dict[int, list] = {}
    for ref in parsed.refs:
        source_cols = ref.col1 if ref.type == ">" else ref.col2 if ref.type == "<" else []
        for col in source_cols:
            column_refs.setdefault(id(col), []).append(ref)

    for table in parsed.tables:
        columns = []
        for column in table.columns:
            col_type = column.type
            if hasattr(col_type, "name"):
                col_type = col_type.name

            # Handle references
            references = []
            for ref in column_refs.get(id(column), []):
                if ref.type == ">":
                    references.append((ref.table2.name, ref.col2[0].name))
                else:
                    references.append((ref.table1.name, ref.col1[0].name))

            # Extract note
            note_text = None
            if hasattr(column, "note") and column.note:
                note_text = column.note.text if hasattr(column.note, "text") else str(column.note)

            columns.append(
                ColumnInfo(
                    name=column.name,
                    type=str(col_type),
                    primary_key=column.pk,
                    unique=column.unique,
                    nullable=not column.not_null,
                    default=column.default,
                    references=references,
                    note=note_text,
                )
            )

        # Extract table note
        table_note = None
        if hasattr(table, "note") and table.note:
            table_note = table.note.text if hasattr(table.note, "text") else str(table.note)

        # Build relationships list
        relationships = []
        for column in columns:
            if column.references:
                for target_table, target_col in column.references:
                    relationships.append(
                        RelationshipInfo(
                            column=column.name,
                            target_table=target_table,
                            target_column=target_col,
                            nullable=column.nullable,
                        )
                    )

        tables.append(
            TableInfo(
                name=table.name,
                columns=columns,
                relationships=relationships,
                note=table_note,
            )
        )

    # Override parsed types with raw DBML types when available
    for table in tables:
        table_raw = raw_types.get(table.name, {})
        table_defaults = raw_defaults.get(table.name, {})
        for column in table.columns:
            raw_type = table_raw.get(column.name)
            if raw_type:
                column.type = raw_type
            raw_default = table_defaults.get(column.name)
            if raw_default is not None:
                column.default = raw_default

    return tables


def _iter_column_lines(dbml_content: str) -> Iterator[tuple[str, str]]:
    """Yield ``(table_name, column_line)`` for each column definition in the text.

    Comments are stripped and table headers / notes / indexes / refs are skipped.
    This lightweight scan recovers raw types and defaults that PyDBML normalizes
    away, which is needed for stable round-tripping. Shared by
    :func:`extract_dbml_types` and :func:`extract_dbml_defaults`.
    """
    current_table: str | None = None
    pending_table: str | None = None

    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        table_match = re.match(r"(?i)^table\s+([A-Za-z_][\w]*)", stripped)
        if table_match and current_table is None:
            if "{" in stripped:
                current_table = table_match.group(1)
            else:
                pending_table = table_match.group(1)
            continue

        if pending_table and "{" in stripped:
            current_table = pending_table
            pending_table = None
            continue

        if current_table:
            if stripped.startswith("}"):
                current_table = None
                continue

            if stripped.lower().startswith(("note:", "indexes", "ref")):
                continue

            line_no_comment = stripped.split("//", 1)[0].strip()
            if not line_no_comment:  # pragma: no cover
                continue

            yield current_table, line_no_comment


def extract_dbml_types(dbml_content: str) -> dict[str, dict[str, str]]:
    """Extract raw column types from DBML text for stable round-tripping."""
    table_types: dict[str, dict[str, str]] = {}
    for table_name, line in _iter_column_lines(dbml_content):
        table_types.setdefault(table_name, {})
        tokens = line.split("[", 1)[0].split()
        if len(tokens) < 2:
            continue
        table_types[table_name][tokens[0]] = " ".join(tokens[1:])
    return table_types


def extract_dbml_defaults(dbml_content: str) -> dict[str, dict[str, Any]]:
    """Extract raw defaults from DBML text."""
    table_defaults: dict[str, dict[str, Any]] = {}
    for table_name, line in _iter_column_lines(dbml_content):
        table_defaults.setdefault(table_name, {})
        if "[" not in line or "]" not in line:
            continue

        before_attrs, attrs = line.split("[", 1)
        attrs = attrs.split("]", 1)[0]
        tokens = before_attrs.split()
        if len(tokens) < 2:
            continue

        col_name = tokens[0]
        for part in attrs.split(","):
            if "default" not in part:
                continue
            key, sep, value = part.partition(":")
            if not sep:
                key, sep, value = part.partition("=")
            if key.strip() != "default":
                continue
            table_defaults[table_name][col_name] = _parse_default_value(value)
            break

    return table_defaults


def _parse_default_value(value: str) -> Any:
    """Parse default value from DBML attribute."""
    raw = value.strip().strip("`").strip('"').strip("'")
    lowered = raw.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def parse_dbml_enums(dbml_content: str) -> dict[str, list[str]]:
    """Parse DBML enums into name -> values."""
    enums = _parse_dbml_enums_from_text(dbml_content)
    if enums:
        return enums

    parsed = PyDBML(dbml_content)
    enums = {}
    for enum in getattr(parsed, "enums", []):  # type: ignore[attr-defined]
        name = getattr(enum, "name", None)
        if not name:
            continue
        values: list[str] = []
        items = (
            getattr(enum, "items", None)
            or getattr(enum, "values", None)
            or getattr(enum, "elements", None)
        )
        if items:
            for item in items:
                value = getattr(item, "name", None) or getattr(item, "value", None) or str(item)
                values.append(str(value))
        enums[str(name)] = values
    return enums


def _parse_dbml_enums_from_text(dbml_content: str) -> dict[str, list[str]]:
    """Parse enums from DBML text directly."""
    enums: dict[str, list[str]] = {}
    current: str | None = None

    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        enum_match = re.match(r"(?i)^enum\s+([A-Za-z_][\w]*)", stripped)
        if enum_match and current is None:
            enum_name = enum_match.group(1)
            enums.setdefault(enum_name, [])
            current = enum_name
            continue

        if current:
            if "}" in stripped:
                current = None
                continue
            value = stripped.split("//", 1)[0].strip().strip(",")
            if value:
                enums[current].append(value)

    return enums
