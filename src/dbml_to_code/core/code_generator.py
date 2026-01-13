"""SQLModel code generation from DBML schema."""

from typing import Any, Dict, List, Optional

from ..models.schema import TableInfo
from ..utils.type_mapping import get_python_type, TYPE_MAPPING


def to_class_name(name: str) -> str:
    """Convert snake_case names to PascalCase."""
    return "".join(part.capitalize() for part in name.split("_") if part)


def _format_default_value(value: Any) -> str:
    """Format default value for Python code."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, str):
        return repr(value)
    return str(value)


def generate_single_model(
    table: TableInfo,
    all_tables: List[TableInfo],
    enums: Optional[Dict[str, List[str]]] = None,
) -> str:
    """Generate SQLModel code for a single table.

    Args:
        table: Table information
        all_tables: List of all tables (for relationship context)
        enums: Optional enum definitions

    Returns:
        Generated Python code as string
    """
    enums = enums or {}

    # Collect field descriptions for DESCRIPTIONS dictionary
    field_descriptions = {}
    for column in table.columns:
        if column.note:
            field_descriptions[column.name] = column.note

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
        col.primary_key and get_python_type(col.type) == "str"
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

    # Generate DESCRIPTIONS dictionary if there are any field descriptions
    descriptions_code = ""
    if field_descriptions:
        descriptions_code = "# Field descriptions\n"
        descriptions_code += "DESCRIPTIONS = {\n"
        for field_name in sorted(field_descriptions.keys()):
            desc = field_descriptions[field_name]
            # Escape quotes properly
            desc_escaped = desc.replace('\\', '\\\\').replace('"', '\\"')
            descriptions_code += f'    "{field_name}": "{desc_escaped}",\n'
        descriptions_code += "}\n\n"

    # Separate columns into base fields (non-PK, non-FK) and special fields
    model_code = []

    # Generate Base class with common fields
    base_class_name = f"{table.name.capitalize()}Base"
    base_class_def = [f"class {base_class_name}(SQLModel):"]
    has_base_fields = False

    for column in table.columns:
        # Skip primary keys for base class
        if column.primary_key:
            continue

        has_base_fields = True
        field_type = get_python_type(column.type)
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

        # Use DESCRIPTIONS dictionary if field has description
        if column.name in field_descriptions:
            field_args.append(f'description=DESCRIPTIONS["{column.name}"]')

        field_str = f"    {column.name}: {field_type}"
        if field_args:
            field_str += f" = Field({', '.join(field_args)})"

        base_class_def.append(field_str)

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

        field_type = get_python_type(column.type)
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

        # Use DESCRIPTIONS dictionary if field has description
        if column.name in field_descriptions:
            field_args.append(f'description=DESCRIPTIONS["{column.name}"]')

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
        field_type = get_python_type(column.type)
        if column.type in enums:
            field_type = to_class_name(column.type)
        field_type = f"Optional[{field_type}]"

        field_args = []
        # Use DESCRIPTIONS dictionary if field has description
        if column.name in field_descriptions:
            field_args.append(f'description=DESCRIPTIONS["{column.name}"]')

        field_str = f"    {column.name}: {field_type}"
        if field_args:
            field_str += f" = Field(default=None, {', '.join(field_args)})"
        else:
            field_str += " = None"

        update_class_def.append(field_str)

    if not update_has_fields:
        update_class_def.append("    pass")

    model_code.append("\n".join(update_class_def) + "\n")

    return imports + descriptions_code + "\n".join(model_code)
