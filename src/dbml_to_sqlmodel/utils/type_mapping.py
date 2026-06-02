"""Type mapping between DBML and Python/SQLModel."""

# DBML type -> Python type mapping
TYPE_MAPPING: dict[str, str] = {
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
    "date": "date",
    "datetime": "datetime",
    "timestamp": "datetime",
    "timestamptz": "datetime",
    "time": "time",
    "float": "float",
    "double": "float",
    "decimal": "float",
    "json": "dict",
}

# Python types that require an import from the standard library ``datetime`` module.
DATETIME_TYPES: frozenset[str] = frozenset({"datetime", "date", "time"})


def get_python_type(dbml_type: str) -> str:
    """Get Python type for a DBML type.

    Args:
        dbml_type: DBML type string

    Returns:
        Python type string (defaults to "str" if not found)
    """
    return TYPE_MAPPING.get(dbml_type.lower(), "str")


def get_datetime_imports(python_types: set[str]) -> list[str]:
    """Return the sorted ``datetime`` names that must be imported for these types.

    Args:
        python_types: Set of Python type names used in a generated module

    Returns:
        Sorted list of names to import from the ``datetime`` module
        (e.g. ``["date", "datetime"]``)
    """
    return sorted(DATETIME_TYPES & python_types)


def is_auto_increment_type(dbml_type: str) -> bool:
    """Check if DBML type is auto-incrementing.

    Args:
        dbml_type: DBML type string

    Returns:
        True if type is auto-incrementing (serial variants)
    """
    return dbml_type.lower() in {"serial", "serial4", "serial8", "bigserial"}
