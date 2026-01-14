"""PyDBML library adapter."""

from typing import Any


def setdefaultattr(obj: Any, name: str, value: Any) -> Any:
    """Get attribute if exists, else set to default and get.

    This is a helper function for working with PyDBML objects
    which may not have all attributes set.

    Args:
        obj: Object to check/modify
        name: Attribute name
        value: Default value to set if attribute doesn't exist

    Returns:
        Attribute value (existing or newly set default)
    """
    if not hasattr(obj, name):
        setattr(obj, name, value)
    return getattr(obj, name)
