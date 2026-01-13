"""Type mapping between DBML and Python/SQLModel."""

from typing import Dict

# DBML type -> Python type mapping
TYPE_MAPPING: Dict[str, str] = {
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


def get_python_type(dbml_type: str) -> str:
    """Get Python type for a DBML type.

    Args:
        dbml_type: DBML type string

    Returns:
        Python type string (defaults to "str" if not found)
    """
    return TYPE_MAPPING.get(dbml_type.lower(), "str")


def is_auto_increment_type(dbml_type: str) -> bool:
    """Check if DBML type is auto-incrementing.

    Args:
        dbml_type: DBML type string

    Returns:
        True if type is auto-incrementing (serial variants)
    """
    return dbml_type.lower() in {"serial", "serial4", "serial8", "bigserial"}
