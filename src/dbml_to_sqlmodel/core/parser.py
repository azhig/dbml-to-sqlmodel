"""DBML parsing functionality."""

import re
import warnings
from typing import Any

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


from ..integrations import setdefaultattr
from ..models.schema import ColumnInfo, RelationshipInfo, TableInfo


def parse_dbml(dbml_content: str) -> list[TableInfo]:
    """Parse DBML content using PyDBML into structured table definitions."""
    raw_types = extract_dbml_types(dbml_content)
    raw_defaults = extract_dbml_defaults(dbml_content)
    parsed = PyDBML(dbml_content)
    tables = []

    # Process references first to handle foreign keys
    for ref in parsed.refs:  # type: ignore
        if ref.type == ">":
            for col in ref.col1:
                col_refs = setdefaultattr(col, "references", [])
                col_refs.append(ref)
        elif ref.type == "<":
            for col in ref.col2:
                col_refs = setdefaultattr(col, "references", [])
                col_refs.append(ref)

    for table in parsed.tables:  # type: ignore
        columns = []
        for column in table.columns:
            col_type = column.type
            if hasattr(col_type, "name"):
                col_type = col_type.name  # type: ignore

            # Handle references
            references = []
            if hasattr(column, "references"):
                for ref in column.references:  # type: ignore
                    if ref.type == ">":
                        target_table = ref.table2.name
                        target_col = ref.col2[0].name
                    else:
                        target_table = ref.table1.name
                        target_col = ref.col1[0].name
                    references.append((target_table, target_col))

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


def extract_dbml_types(dbml_content: str) -> dict[str, dict[str, str]]:
    """Extract raw column types from DBML text for stable round-tripping."""
    table_types: dict[str, dict[str, str]] = {}
    current_table: str | None = None
    pending_table: str | None = None

    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        table_match = re.match(r"(?i)^table\s+([A-Za-z_][\w]*)", stripped)
        if table_match and current_table is None:
            table_name = table_match.group(1)
            if "{" in stripped:
                current_table = table_name
                table_types.setdefault(current_table, {})
            else:
                pending_table = table_name
            continue

        if pending_table and "{" in stripped:
            current_table = pending_table
            pending_table = None
            table_types.setdefault(current_table, {})
            continue

        if current_table:
            if stripped.startswith("}"):
                current_table = None
                continue

            lowered = stripped.lower()
            if (
                lowered.startswith("note:")
                or lowered.startswith("indexes")
                or lowered.startswith("ref")
            ):
                continue

            line_no_comment = stripped.split("//", 1)[0].strip()
            if not line_no_comment:  # pragma: no cover
                continue

            parts = line_no_comment.split("[", 1)[0].strip()
            tokens = parts.split()
            if len(tokens) < 2:
                continue

            col_name = tokens[0]
            col_type = " ".join(tokens[1:])
            table_types[current_table][col_name] = col_type

    return table_types


def extract_dbml_defaults(dbml_content: str) -> dict[str, dict[str, Any]]:
    """Extract raw defaults from DBML text."""
    table_defaults: dict[str, dict[str, Any]] = {}
    current_table: str | None = None
    pending_table: str | None = None

    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        table_match = re.match(r"(?i)^table\s+([A-Za-z_][\w]*)", stripped)
        if table_match and current_table is None:
            table_name = table_match.group(1)
            if "{" in stripped:
                current_table = table_name
                table_defaults.setdefault(current_table, {})
            else:
                pending_table = table_name
            continue

        if pending_table and "{" in stripped:
            current_table = pending_table
            pending_table = None
            table_defaults.setdefault(current_table, {})
            continue

        if current_table:
            if stripped.startswith("}"):
                current_table = None
                continue

            lowered = stripped.lower()
            if (
                lowered.startswith("note:")
                or lowered.startswith("indexes")
                or lowered.startswith("ref")
            ):
                continue

            line_no_comment = stripped.split("//", 1)[0].strip()
            if not line_no_comment:  # pragma: no cover
                continue

            if "[" not in line_no_comment or "]" not in line_no_comment:
                continue

            before_attrs, attrs = line_no_comment.split("[", 1)
            attrs = attrs.split("]", 1)[0]
            tokens = before_attrs.split()
            if len(tokens) < 2:
                continue

            col_name = tokens[0]
            for part in attrs.split(","):
                if "default" not in part:
                    continue
                key, _, value = part.partition(":")
                if not _:
                    key, _, value = part.partition("=")
                if key.strip() != "default":
                    continue
                default_value = _parse_default_value(value)
                table_defaults[current_table][col_name] = default_value
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
