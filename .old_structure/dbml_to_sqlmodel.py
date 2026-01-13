import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from pydbml import PyDBML


def setdefaultattr(obj, name: str, value: Any) -> Any:
    """Get attribute if exists, else set to default and get"""
    if not hasattr(obj, name):
        setattr(obj, name, value)
    return getattr(obj, name)


@dataclass
class ColumnInfo:
    name: str
    type: str
    primary_key: bool
    unique: bool
    nullable: bool
    default: Any = None
    references: Optional[List] = None
    note: Optional[str] = None


@dataclass
class RelationshipInfo:
    """Information about a foreign key relationship."""
    column: str
    target_table: str
    target_column: str
    nullable: bool


@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo]
    relationships: List[RelationshipInfo] = None
    note: Optional[str] = None

    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []


def parse_dbml(dbml_content: str) -> List[TableInfo]:
    """Parse DBML content using PyDBML into structured table definitions"""
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
                note_text = (
                    column.note.text
                    if hasattr(column.note, "text")
                    else str(column.note)
                )

            columns.append(
                ColumnInfo(
                    name=column.name,
                    type=str(col_type),
                    primary_key=column.pk,
                    unique=column.unique,
                    nullable=not column.not_null,
                    default=column.default,
                    references=references,
                    note=note_text,  # Keep note
                )
            )

        # Extract table note
        table_note = None
        if hasattr(table, "note") and table.note:
            table_note = (
                table.note.text
                if hasattr(table.note, "text")
                else str(table.note)
            )

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


 


def to_class_name(name: str) -> str:
    """Convert snake_case names to PascalCase."""
    return "".join(part.capitalize() for part in name.split("_") if part)


def extract_dbml_types(dbml_content: str) -> dict[str, dict[str, str]]:
    """Extract raw column types from DBML text for stable round-tripping."""
    table_types: dict[str, dict[str, str]] = {}
    current_table: Optional[str] = None
    pending_table: Optional[str] = None

    for line in dbml_content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue

        table_match = re.match(r"(?i)^table\\s+([A-Za-z_][\\w]*)", stripped)
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
            if lowered.startswith("note:") or lowered.startswith("indexes") or lowered.startswith("ref"):
                continue

            line_no_comment = stripped.split("//", 1)[0].strip()
            if not line_no_comment:
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
    current_table: Optional[str] = None
    pending_table: Optional[str] = None

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
            if lowered.startswith("note:") or lowered.startswith("indexes") or lowered.startswith("ref"):
                continue

            line_no_comment = stripped.split("//", 1)[0].strip()
            if not line_no_comment:
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


def generate_sqlmodel(tables: List[TableInfo]) -> str:
    """Generate SQLModel code from parsed tables"""
    imports = """from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    pass  # Relationships will be added here

"""
    model_code = []
    create_schemas = []
    update_schemas = []

    # Map table name to relationships
    table_relationships = {}

    type_mapping = {
        "int": "int",
        "integer": "int",
        "serial": "int",
        "serial4": "int",
        "serial8": "int",
        "bigserial": "int",
        "bigint": "int",
        "varchar": "str",
        "text": "str",
        "string": "str",
        "bool": "bool",
        "boolean": "bool",
        "date": "str",
        "datetime": "str",
        "timestamp": "str",
        "float": "float",
        "double": "float",
        "decimal": "float",
        "json": "dict",
    }

    # Collect relationships first
    for table in tables:
        table_relationships[table.name] = []
        for column in table.columns:
            if column.references:
                target_table, target_col = column.references[0]
                if target_table != table.name or target_col != column.name:
                    # Create relationship
                    rel_name = target_table.rstrip("s")  # Drop trailing "s"
                    table_relationships[table.name].append(
                        (column.name, rel_name, target_table)
                    )

    # Generate main models first
    for table in tables:
        class_def = [f"class {table.name.capitalize()}(SQLModel, table=True):"]

        for column in table.columns:
            field_type = type_mapping.get(column.type.lower(), "str")

            # Handle nullable fields
            if column.nullable and not column.primary_key:
                field_type = f"Optional[{field_type}]"

            # Build Field parameters
            field_args = []
            if column.primary_key:
                if field_type == "int":
                    field_type = "Optional[int]"
                    field_args.append("default=None")
                    field_args.append("primary_key=True")
                elif field_type == "str":
                    field_args.append("default_factory=lambda: str(uuid.uuid4())")
                    field_args.append("primary_key=True")
                else:
                    field_args.append("primary_key=True")
            if column.unique:
                field_args.append("unique=True")
            if column.references:
                target_table, target_col = column.references[0]
                if target_table == table.name and target_col == column.name:
                    continue
                if target_table and target_col:
                    # Add default=None for nullable FKs
                    if column.nullable:
                        field_args.insert(0, "default=None")
                    field_args.append(f"foreign_key='{target_table}.{target_col}'")

            # After field_args creation in the field generation loop
            if column.note:
                # Escape quotes in descriptions
                note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
                field_args.append(f'description="{note_escaped}"')

            # Format the field definition
            field_str = f"    {column.name}: {field_type}"
            if field_args:
                field_str += f" = Field({', '.join(field_args)})"

            class_def.append(field_str)

        # Add relationships
        if table.name in table_relationships:
            class_def.append("")  # Spacer for readability
            for fk_col, rel_name, target_table in table_relationships[table.name]:
                target_class = target_table.capitalize()
                # Check nullable
                is_nullable = any(
                    c.name == fk_col and c.nullable for c in table.columns
                )
                rel_type = (
                    f'Optional["{target_class}"]'
                    if is_nullable
                    else f'"{target_class}"'
                )
                class_def.append(f"    {rel_name}: {rel_type} = Relationship()")

        model_code.append("\n".join(class_def) + "\n")

    # Generate Create schemas
    for table in tables:
        create_class_def = [f"class {table.name.capitalize()}Create(BaseModel):"]

        # Add class docstring
        if any(c.note for c in table.columns):
            create_class_def.append(f'    """Create schema for {table.name}."""')

        for column in table.columns:
            # Skip primary key fields that are auto-increment
            if column.primary_key and column.default is None:
                continue

            field_type = type_mapping.get(column.type.lower(), "str")

            # Handle nullable fields
            if column.nullable and not column.primary_key:
                field_type = f"Optional[{field_type}]"

            # Build Field parameters
            field_args = []

            # Add description from note
            if column.note:
                note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
                field_args.append(f'description="{note_escaped}"')

            if column.unique:
                field_args.append("unique=True")

            # Format the field definition
            field_str = f"    {column.name}: {field_type}"
            if field_args:
                field_str += f" = Field({', '.join(field_args)})"

            create_class_def.append(field_str)

        # Add ellipsis if class is empty
        if len(create_class_def) == 1:
            create_class_def.append("    ...")

        create_schemas.append("\n".join(create_class_def) + "\n")

    # Generate Update schemas
    for table in tables:
        update_class_def = [f"class {table.name.capitalize()}Update(BaseModel):"]

        # Add class docstring
        if any(c.note for c in table.columns):
            update_class_def.append(f'    """Update schema for {table.name}."""')

        for column in table.columns:
            # Skip primary key fields
            if column.primary_key:
                continue

            field_type = type_mapping.get(column.type.lower(), "str")
            field_type = f"Optional[{field_type}]"  # All fields optional in update

            # Build Field parameters
            field_args = []

            # Add description from note
            if column.note:
                note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
                field_args.append(f'description="{note_escaped}"')

            if column.unique:
                field_args.append("unique=True")

            # Format the field definition
            field_str = f"    {column.name}: {field_type}"
            if field_args:
                field_str += f" = Field({', '.join(field_args)})"

            # Add field to class definition
            update_class_def.append(field_str)

        # Add ellipsis if class is empty
        if len(update_class_def) == 1:
            update_class_def.append("    ...")

        update_schemas.append("\n".join(update_class_def) + "\n")

    # Combine all parts
    return imports + "\n\n".join(model_code + create_schemas + update_schemas)


def _format_default_value(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return repr(value)
    return str(value)


def _parse_dbml_enums_from_text(dbml_content: str) -> Dict[str, List[str]]:
    enums: Dict[str, List[str]] = {}
    current: Optional[str] = None

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


def parse_dbml_enums(dbml_content: str) -> Dict[str, List[str]]:
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
        values: List[str] = []
        items = getattr(enum, "items", None) or getattr(enum, "values", None) or getattr(enum, "elements", None)
        if items:
            for item in items:
                value = getattr(item, "name", None) or getattr(item, "value", None) or str(item)
                values.append(str(value))
        enums[str(name)] = values
    return enums


def generate_single_model(
    table: TableInfo,
    all_tables: List[TableInfo],
    enums: Optional[Dict[str, List[str]]] = None,
) -> str:
    """Generate SQLModel code for a single table"""

    type_mapping = {
        "int": "int",
        "integer": "int",
        "serial": "int",
        "serial4": "int",
        "serial8": "int",
        "bigserial": "int",
        "bigint": "int",
        "varchar": "str",
        "text": "str",
        "string": "str",
        "bool": "bool",
        "boolean": "bool",
        "date": "str",
        "datetime": "str",
        "timestamp": "str",
        "float": "float",
        "double": "float",
        "decimal": "float",
        "json": "dict",
    }
    enums = enums or {}

    # Collect relationships for this table
    table_relationships = []
    related_models = set()  # Track which models need to be imported
    enum_types = {to_class_name(col.type) for col in table.columns if col.type in enums}

    for column in table.columns:
        if column.references:
            target_table, target_col = column.references[0]
            if target_table != table.name or target_col != column.name:
                rel_name = target_table.rstrip("s")
                table_relationships.append((column.name, rel_name, target_table))
                related_models.add(target_table.capitalize())

    # Check if uuid is needed (for string primary keys)
    needs_uuid = any(
        col.primary_key and type_mapping.get(col.type.lower(), "str") == "str"
        for col in table.columns
    )

    # Generate imports with TYPE_CHECKING block
    sqlmodel_imports = ["SQLModel", "Field"]
    if table_relationships:
        sqlmodel_imports.append("Relationship")

    imports = f"""from sqlmodel import {", ".join(sqlmodel_imports)}
from typing import Optional, TYPE_CHECKING
"""
    if enum_types:
        imports += f"from ..enums import {', '.join(sorted(enum_types))}\n"
    if needs_uuid:
        imports += "import uuid\n"
    imports += "\n"

    if related_models:
        imports += "if TYPE_CHECKING:\n"
        for model in sorted(related_models):
            # Import from sibling module
            model_module = model.lower()
            imports += f"    from ..{model_module}.model import {model}\n"
        imports += "\n"
    else:
        imports += """if TYPE_CHECKING:
    pass  # Relationships will be added here

"""
    # Separate columns into base fields (non-PK, non-FK) and special fields
    model_code = []
    base_fields = []
    pk_fields = []

    # Generate Base class with common fields
    base_class_name = f"{table.name.capitalize()}Base"
    base_class_def = [f"class {base_class_name}(SQLModel):"]
    has_base_fields = False

    for column in table.columns:
        # Skip primary keys and relationship fields for base class
        if column.primary_key:
            continue

        has_base_fields = True
        field_type = type_mapping.get(column.type.lower(), "str")
        if column.type in enums:
            field_type = to_class_name(column.type)

        if column.nullable:
            field_type = f"Optional[{field_type}]"

        field_args = []

        # Defaults
        if column.default is not None:
            field_args.append(f"default={_format_default_value(column.default)}")
        elif column.nullable:
            field_args.append("default=None")

        if column.unique:
            field_args.append("unique=True")

        # Add foreign_key for FK fields
        if column.references:
            target_table, target_col = column.references[0]
            if not (target_table == table.name and target_col == column.name):
                if target_table and target_col:
                    field_args.append(f"foreign_key='{target_table}.{target_col}'")

        if column.note:
            note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
            field_args.append(f'description="{note_escaped}"')

        field_str = f"    {column.name}: {field_type}"
        if field_args:
            field_str += f" = Field({', '.join(field_args)})"

        base_class_def.append(field_str)
        base_fields.append((column.name, field_type, field_args))

    # If no base fields, add pass
    if not has_base_fields:
        base_class_def.append("    pass")

    model_code.append("\n".join(base_class_def) + "\n")

    # Generate main table model (inherits from Base)
    table_class_name = table.name.capitalize()
    class_def = [f"class {table_class_name}({base_class_name}, table=True):"]
    if table.note:
        note_escaped = table.note.replace('"""', '\\"\\"\\"')
        class_def.append(f'    """{note_escaped}"""')

    # Add primary key fields
    for column in table.columns:
        if not column.primary_key:
            continue

        field_type = type_mapping.get(column.type.lower(), "str")
        if column.type in enums:
            field_type = to_class_name(column.type)
        field_args = []

        if field_type == "int":
            field_type = "Optional[int]"
            field_args.append("default=None")
            field_args.append("primary_key=True")
        elif field_type == "str":
            field_args.append("default_factory=lambda: str(uuid.uuid4())")
            field_args.append("primary_key=True")
        else:
            field_args.append("primary_key=True")

        if column.note:
            note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
            field_args.append(f'description="{note_escaped}"')

        field_str = f"    {column.name}: {field_type}"
        if field_args:
            field_str += f" = Field({', '.join(field_args)})"

        class_def.append(field_str)

    # Add relationships
    if table_relationships:
        if len(class_def) == 1:
            class_def.append("")
        else:
            class_def.append("")
        for fk_col, rel_name, target_table in table_relationships:
            target_class = target_table.capitalize()
            is_nullable = any(c.name == fk_col and c.nullable for c in table.columns)
            rel_type = (
                f'Optional["{target_class}"]' if is_nullable else f'"{target_class}"'
            )
            class_def.append(f"    {rel_name}: {rel_type} = Relationship()")

    # If only relationships and no PK, ensure proper formatting
    if len(class_def) == 1 and not table_relationships:
        class_def.append("    pass")

    model_code.append("\n".join(class_def) + "\n")

    # Generate Create schema (inherits from Base, all fields as-is)
    create_class_def = [f"class {table_class_name}Create({base_class_name}):"]
    create_class_def.append(f'    """Create schema for {table.name}."""')
    create_class_def.append("    pass")

    model_code.append("\n".join(create_class_def) + "\n")

    # Generate Update schema (inherits from Base but all Optional)
    update_class_def = [f"class {table_class_name}Update(SQLModel):"]
    update_class_def.append(f'    """Update schema for {table.name}."""')

    # Re-declare all base fields as Optional
    update_has_fields = False
    for column in table.columns:
        if column.primary_key:
            continue

        update_has_fields = True
        field_type = type_mapping.get(column.type.lower(), "str")
        if column.type in enums:
            field_type = to_class_name(column.type)
        field_type = f"Optional[{field_type}]"

        field_args = []
        if column.note:
            note_escaped = column.note.replace('"', '\\"').replace("'", "\\'")
            field_args.append(f'description="{note_escaped}"')

        field_str = f"    {column.name}: {field_type}"
        if field_args:
            field_str += f" = Field(default=None, {', '.join(field_args)})"
        else:
            field_str += " = None"

        update_class_def.append(field_str)

    if not update_has_fields:
        update_class_def.append("    pass")

    model_code.append("\n".join(update_class_def) + "\n")

    return imports + "\n\n".join(model_code)
