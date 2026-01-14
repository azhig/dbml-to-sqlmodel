"""Reverse conversion from generated SQLModel code to DBML."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from .core import parse_dbml
from .models import ColumnInfo, TableInfo

_PYTHON_TO_DBML_TYPES = {
    "int": "integer",
    "str": "text",
    "bool": "bool",
    "float": "float",
    "dict": "json",
}

_DBML_TYPE_EQUIVALENCE = {
    "integer": {"int", "integer", "serial", "serial4", "serial8", "bigserial", "bigint"},
    "text": {"text", "varchar", "string", "date", "datetime", "timestamp"},
    "bool": {"bool", "boolean"},
    "float": {"float", "double", "decimal"},
    "json": {"json"},
}


def _canonical_dbml_type(dbml_type: str) -> str:
    lower = dbml_type.lower()
    for canonical, values in _DBML_TYPE_EQUIVALENCE.items():
        if lower in values:
            return canonical
    return lower


@dataclass
class _ParsedColumn:
    name: str
    type_name: str
    nullable: bool
    primary_key: bool
    unique: bool
    foreign_key: str | None
    description: str | None
    default: object | None
    default_factory: str | None


def _annotation_to_type(annotation: ast.expr) -> tuple[str, bool]:
    """Return (type_name, is_optional) from annotation."""
    if isinstance(annotation, ast.Subscript):
        value = annotation.value
        if isinstance(value, ast.Name) and value.id == "Optional":
            inner = annotation.slice
            if isinstance(inner, ast.Name):
                return inner.id, True
            if isinstance(inner, ast.Attribute):
                return inner.attr, True
    if isinstance(annotation, ast.Name):
        return annotation.id, False
    if isinstance(annotation, ast.Attribute):
        return annotation.attr, False
    return "str", False


def _parse_field_kwargs(
    call: ast.Call, dict_constants: dict[str, dict] = None
) -> dict[str, object]:
    """Parse Field() keyword arguments.

    Args:
        call: AST Call node for Field()
        dict_constants: Optional dict mapping variable names to their constant values
                       (e.g., {"DESCRIPTIONS": {"username": "Unique username"}})
    """
    if dict_constants is None:
        dict_constants = {}

    kwargs: dict[str, object] = {}
    for kw in call.keywords:
        if kw.arg is None:
            continue
        if isinstance(kw.value, ast.Constant):
            kwargs[kw.arg] = kw.value.value
        elif isinstance(kw.value, ast.Name):
            kwargs[kw.arg] = kw.value.id
        elif isinstance(kw.value, ast.Subscript):
            # Handle dictionary subscript: DESCRIPTIONS["username"]
            if isinstance(kw.value.value, ast.Name) and isinstance(kw.value.slice, ast.Constant):
                dict_name = kw.value.value.id
                key = kw.value.slice.value
                if dict_name in dict_constants and key in dict_constants[dict_name]:
                    kwargs[kw.arg] = dict_constants[dict_name][key]
                else:
                    kwargs[kw.arg] = None
            else:
                kwargs[kw.arg] = None
        elif isinstance(kw.value, ast.Lambda):
            kwargs[kw.arg] = "lambda"
        elif isinstance(kw.value, ast.Call) and isinstance(kw.value.func, ast.Name):
            kwargs[kw.arg] = kw.value.func.id
        else:
            kwargs[kw.arg] = None
    return kwargs


def _extract_dict_constants(tree: ast.Module) -> dict[str, dict]:
    """Extract dictionary constants from module level.

    Returns dict mapping variable names to their constant dict values.
    Example: {"DESCRIPTIONS": {"username": "Unique username", ...}}
    """
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Dict):
                # Extract dict constant
                dict_value = {}
                for key_node, value_node in zip(node.value.keys, node.value.values):
                    if isinstance(key_node, ast.Constant) and isinstance(value_node, ast.Constant):
                        dict_value[key_node.value] = value_node.value
                if dict_value:
                    constants[target.id] = dict_value
    return constants


def _extract_columns(
    class_def: ast.ClassDef, dict_constants: dict[str, dict] = None
) -> list[_ParsedColumn]:
    """Extract columns from a ClassDef node.

    Args:
        class_def: AST ClassDef node
        dict_constants: Optional dict of constant dictionaries from module level
    """
    if dict_constants is None:
        dict_constants = {}

    columns: list[_ParsedColumn] = []
    for node in class_def.body:
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        if node.value is None:
            field_kwargs: dict[str, object] = {}
        elif isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "Relationship":
                continue
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "Field":
                field_kwargs = _parse_field_kwargs(node.value, dict_constants)
            else:
                continue
        else:
            continue

        type_name, is_optional = _annotation_to_type(node.annotation)
        columns.append(
            _ParsedColumn(
                name=node.target.id,
                type_name=type_name,
                nullable=is_optional,
                primary_key=bool(field_kwargs.get("primary_key", False)),
                unique=bool(field_kwargs.get("unique", False)),
                foreign_key=field_kwargs.get("foreign_key"),
                description=field_kwargs.get("description"),
                default=field_kwargs.get("default"),
                default_factory=field_kwargs.get("default_factory"),
            )
        )
    return columns


def _model_files(models_dir: Path) -> Iterable[Path]:
    if not models_dir.exists():
        return []
    return sorted(models_dir.glob("*/model.py"))


def _table_name_from_path(model_file: Path) -> str:
    return model_file.parent.name


def _load_enum_map(models_dir: Path) -> dict[str, str]:
    enums_path = models_dir / "enums.py"
    if not enums_path.exists():
        return {}

    tree = ast.parse(enums_path.read_text(encoding="utf-8"))
    enum_map: dict[str, str] = {}

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(isinstance(base, ast.Name) and base.id == "Enum" for base in node.bases):
            continue

        dbml_name = None
        for stmt in node.body:
            if (
                isinstance(stmt, ast.Assign)
                and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)
            ):
                if stmt.targets[0].id == "__dbml_name__" and isinstance(stmt.value, ast.Constant):
                    dbml_name = str(stmt.value.value)
                    break
        if dbml_name:
            enum_map[node.name] = dbml_name

    return enum_map


def _parse_model_file(model_file: Path, enum_map: dict[str, str]) -> TableInfo:
    tree = ast.parse(model_file.read_text(encoding="utf-8"))

    # Extract dictionary constants (like DESCRIPTIONS = {...})
    dict_constants = _extract_dict_constants(tree)

    class_map = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    table_class = None
    for class_def in class_map.values():
        if any(
            kw.arg == "table" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in class_def.keywords
        ):
            table_class = class_def
            break

    if table_class is None:
        raise ValueError(f"No table class found in {model_file}")

    table_note = ast.get_docstring(table_class)

    base_class_name = None
    if table_class.bases and isinstance(table_class.bases[0], ast.Name):
        base_class_name = table_class.bases[0].id

    base_columns: list[_ParsedColumn] = []
    if base_class_name and base_class_name in class_map:
        base_columns = _extract_columns(class_map[base_class_name], dict_constants)

    table_columns = _extract_columns(table_class, dict_constants)

    dbml_columns: list[ColumnInfo] = []
    seen = set()
    for column in table_columns + base_columns:
        if column.name in seen:
            continue
        seen.add(column.name)

        if column.type_name in enum_map:
            dbml_type = enum_map[column.type_name]
        else:
            dbml_type = _PYTHON_TO_DBML_TYPES.get(column.type_name, "text")
        is_nullable = column.nullable
        if column.primary_key:
            is_nullable = False

        references = None
        if column.foreign_key:
            references = [tuple(str(column.foreign_key).split(".", 1))]

        note = column.description
        default_value = column.default

        dbml_columns.append(
            ColumnInfo(
                name=column.name,
                type=dbml_type,
                primary_key=column.primary_key,
                unique=column.unique,
                nullable=is_nullable,
                default=None if default_value in (None, "None") else default_value,
                references=references,
                note=note,
            )
        )

    return TableInfo(
        name=_table_name_from_path(model_file),
        columns=dbml_columns,
        relationships=[],
        note=table_note,
    )


def generate_dbml_from_models(models_dir: Path) -> str:
    """Generate DBML content from generated SQLModel code."""
    tables = []
    enum_map = _load_enum_map(models_dir)
    for model_file in _model_files(models_dir):
        tables.append(_parse_model_file(model_file, enum_map))

    if not tables:
        raise ValueError(f"No model files found in {models_dir}")

    return build_dbml(tables)


def apply_schema_hints(generated_dbml: str, schema_dbml: str) -> str:
    """Apply types/defaults from schema DBML to generated DBML when names match."""
    generated_tables = parse_dbml(generated_dbml)
    schema_tables = parse_dbml(schema_dbml)

    schema_map: dict[str, dict[str, ColumnInfo]] = {}
    for table in schema_tables:
        schema_map[table.name] = {col.name: col for col in table.columns}

    for table in generated_tables:
        table_schema = schema_map.get(table.name, {})
        for col in table.columns:
            schema_col = table_schema.get(col.name)
            if not schema_col:
                continue
            col.type = schema_col.type
            if schema_col.default is not None:
                col.default = schema_col.default

    return build_dbml(generated_tables)


_TABLE_HEADER_RE = re.compile(r"^\s*table\s+([A-Za-z_][\w]*)\b", re.IGNORECASE)
_COLUMN_LINE_RE = re.compile(r"^\s+([A-Za-z_][\w]*)\s+\S+")


def _format_dbml_column(column: ColumnInfo) -> str:
    attrs = []
    if column.primary_key:
        attrs.append("primary key")
    if not column.nullable and not column.primary_key:
        attrs.append("not null")
    if column.unique:
        attrs.append("unique")
    if column.default is not None:
        if isinstance(column.default, str):
            attrs.append(f'default: "{column.default}"')
        else:
            attrs.append(f"default: {column.default}")
    if column.references:
        for target_table, target_col in column.references:
            attrs.append(f"ref: > {target_table}.{target_col}")
    if column.note:
        note = column.note.replace('"', '\\"')
        attrs.append(f'note: "{note}"')

    if attrs:
        return f"  {column.name} {column.type} [{', '.join(attrs)}]"
    return f"  {column.name} {column.type}"


def _format_table_header(table: TableInfo) -> str:
    if table.note:
        note = table.note.replace('"', '\\"')
        return f'Table {table.name} [note: "{note}"] {{'
    return f"Table {table.name} {{"


def _format_table_header_like(existing_line: str, table: TableInfo) -> str:
    indent = existing_line[: len(existing_line) - len(existing_line.lstrip())]
    stripped = existing_line.lstrip()
    keyword = "table" if stripped.startswith("table") else "Table"
    if table.note:
        note = table.note.replace('"', '\\"')
        return f'{indent}{keyword} {table.name} [note: "{note}"] {{'
    return f"{indent}{keyword} {table.name} {{"


def _columns_equivalent(left: ColumnInfo, right: ColumnInfo) -> bool:
    if _canonical_dbml_type(left.type) != _canonical_dbml_type(right.type):
        return False
    if left.primary_key != right.primary_key:
        return False
    if left.unique != right.unique:
        return False
    if left.nullable != right.nullable:
        return False
    if left.default != right.default:
        return False
    if (left.references or []) != (right.references or []):
        return False
    if left.note != right.note:
        return False
    return True


def apply_dbml_changes(existing_dbml: str, generated_dbml: str) -> str:
    """Apply table/column changes to existing DBML without rewriting the whole file."""
    existing_tables = parse_dbml(existing_dbml)
    generated_tables = parse_dbml(generated_dbml)

    existing_table_map = {table.name: table for table in existing_tables}
    generated_table_map = {table.name: table for table in generated_tables}

    lines = existing_dbml.splitlines()
    table_spans: list[tuple[str, int, int]] = []
    idx = 0
    while idx < len(lines):
        match = _TABLE_HEADER_RE.match(lines[idx])
        if not match:
            idx += 1
            continue
        table_name = match.group(1)
        start = idx
        idx += 1
        while idx < len(lines) and lines[idx].strip() != "}":
            idx += 1
        if idx < len(lines):
            end = idx
            table_spans.append((table_name, start, end))
        idx += 1

    spans_by_start = {start: (name, start, end) for name, start, end in table_spans}

    updated_lines: list[str] = []
    idx = 0
    while idx < len(lines):
        if idx in spans_by_start:
            name, start, end = spans_by_start[idx]
            generated_table = generated_table_map.get(name)
            existing_table = existing_table_map.get(name)
            if not generated_table or not existing_table:
                updated_lines.extend(lines[start : end + 1])
                idx = end + 1
                continue

            header_line = lines[start]
            if (existing_table.note or "") != (generated_table.note or ""):
                header_line = _format_table_header_like(lines[start], generated_table)
            block_lines = lines[start + 1 : end]
            line_map: dict[str, str] = {}
            for line in block_lines:
                col_match = _COLUMN_LINE_RE.match(line)
                if col_match:
                    line_map[col_match.group(1)] = line
            non_column_lines = [line for line in block_lines if not _COLUMN_LINE_RE.match(line)]

            existing_cols = {col.name: col for col in existing_table.columns}
            generated_line_map: dict[str, str] = {}
            for col in generated_table.columns:
                existing_col = existing_cols.get(col.name)
                if existing_col and _columns_equivalent(existing_col, col):
                    generated_line_map[col.name] = line_map.get(col.name, _format_dbml_column(col))
                else:
                    generated_line_map[col.name] = _format_dbml_column(col)

            # Preserve non-column lines (notes, comments, blank lines) in place.
            rebuilt_lines: list[str] = [
                generated_line_map[col.name]
                for col in generated_table.columns
                if col.name in generated_line_map
            ]
            rebuilt_lines.extend(non_column_lines)

            updated_lines.append(header_line)
            updated_lines.extend(rebuilt_lines)
            updated_lines.append(lines[end])
            idx = end + 1
            continue

        updated_lines.append(lines[idx])
        idx += 1

    if generated_table_map:
        existing_names = {name for name, _, _ in table_spans}
        new_tables = [t for t in generated_tables if t.name not in existing_names]
        if new_tables:
            if updated_lines and updated_lines[-1].strip():
                updated_lines.append("")
            for table in new_tables:
                updated_lines.extend(build_dbml([table]).splitlines())
                updated_lines.append("")
            if updated_lines and updated_lines[-1] == "":
                updated_lines.pop()

    return "\n".join(updated_lines).rstrip() + "\n"


def apply_dbml_table_updates(existing_dbml: str, generated_dbml: str) -> str:
    """Replace only changed table blocks with normalized versions."""
    existing_tables = parse_dbml(existing_dbml)
    generated_tables = parse_dbml(generated_dbml)

    existing_table_map = {table.name: table for table in existing_tables}
    generated_table_map = {table.name: table for table in generated_tables}

    def table_block_lines(table: TableInfo) -> list[str]:
        block = build_dbml([table]).splitlines()
        if block and block[-1] == "":  # pragma: no cover
            block.pop()
        return block

    normalized_existing_blocks = {
        name: "\n".join(table_block_lines(table)) for name, table in existing_table_map.items()
    }
    normalized_generated_blocks = {
        name: "\n".join(table_block_lines(table)) for name, table in generated_table_map.items()
    }

    lines = existing_dbml.splitlines()
    table_spans: list[tuple[str, int, int]] = []
    idx = 0
    while idx < len(lines):
        match = _TABLE_HEADER_RE.match(lines[idx])
        if not match:
            idx += 1
            continue
        table_name = match.group(1)
        start = idx
        idx += 1
        while idx < len(lines) and lines[idx].strip() != "}":
            idx += 1
        if idx < len(lines):
            end = idx
            table_spans.append((table_name, start, end))
        idx += 1

    spans_by_start = {start: (name, start, end) for name, start, end in table_spans}
    updated_lines: list[str] = []
    idx = 0
    while idx < len(lines):
        if idx in spans_by_start:
            name, start, end = spans_by_start[idx]
            if name in normalized_generated_blocks:
                existing_block = normalized_existing_blocks.get(name, "")
                generated_block = normalized_generated_blocks[name]
                if existing_block != generated_block:
                    updated_lines.extend(table_block_lines(generated_table_map[name]))
                else:
                    updated_lines.extend(lines[start : end + 1])
            else:
                updated_lines.extend(lines[start : end + 1])
            idx = end + 1
            continue
        updated_lines.append(lines[idx])
        idx += 1

    existing_names = {name for name, _, _ in table_spans}
    new_tables = [t for t in generated_tables if t.name not in existing_names]
    if new_tables:
        if updated_lines and updated_lines[-1].strip():
            updated_lines.append("")
        for table in new_tables:
            updated_lines.extend(table_block_lines(table))
            updated_lines.append("")
        if updated_lines and updated_lines[-1] == "":
            updated_lines.pop()

    return "\n".join(updated_lines).rstrip() + "\n"


def normalize_dbml(dbml_content: str) -> str:
    """Normalize DBML content to a stable, formatted output."""
    tables = parse_dbml(dbml_content)
    return build_dbml(tables)


def normalize_dbml_for_compare(dbml_content: str) -> str:
    """Normalize DBML content for comparison, allowing equivalent types."""
    normalized = normalize_dbml(dbml_content)
    return canonicalize_dbml_text(normalized)


def canonicalize_dbml_text(dbml_content: str) -> str:
    """Canonicalize DBML type tokens inside text for comparison."""
    lines: list[str] = []
    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Table ") or stripped.startswith("Ref"):
            lines.append(line)
            continue

        if stripped.startswith("}"):
            lines.append(line)
            continue

        # Only rewrite column lines (indent + name + type)
        if line.lstrip() != line:
            before_attrs = line.split("[", 1)[0].rstrip()
            tokens = before_attrs.split()
            if len(tokens) >= 2:
                col_name = tokens[0]
                col_type = " ".join(tokens[1:])
                canonical = _canonical_dbml_type(col_type)
                indent = " " * (len(line) - len(line.lstrip()))
                rebuilt = line.replace(
                    before_attrs,
                    f"{indent}{col_name} {canonical}",
                    1,
                )
                lines.append(rebuilt)
                continue

        lines.append(line)

    return "\n".join(lines)


def build_dbml(tables: Iterable[TableInfo]) -> str:
    """Build DBML text from TableInfo."""
    lines: list[str] = []
    for table in sorted(tables, key=lambda t: t.name):
        if table.note:
            note = table.note.replace('"', '\\"')
            lines.append(f'Table {table.name} [note: "{note}"] {{')
        else:
            lines.append(f"Table {table.name} {{")
        for column in table.columns:
            attrs = []
            if column.primary_key:
                attrs.append("primary key")
            if not column.nullable and not column.primary_key:
                attrs.append("not null")
            if column.unique:
                attrs.append("unique")
            if column.default is not None:
                if isinstance(column.default, str):
                    attrs.append(f'default: "{column.default}"')
                else:
                    attrs.append(f"default: {column.default}")
            if column.references:
                for target_table, target_col in column.references:
                    attrs.append(f"ref: > {target_table}.{target_col}")
            if column.note:
                note = column.note.replace('"', '\\"')
                attrs.append(f'note: "{note}"')

            if attrs:
                lines.append(f"  {column.name} {column.type} [{', '.join(attrs)}]")
            else:
                lines.append(f"  {column.name} {column.type}")

        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
