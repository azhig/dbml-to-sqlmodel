"""File information models."""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class FileStatus(str, Enum):
    """Status of a generated file."""

    CREATED = "created"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    PROTECTED = "protected"


@dataclass
class FileInfo:
    """Information about a generated file."""

    relative_path: str
    status: FileStatus
    is_protected: bool

    @property
    def status_tuple(self) -> Tuple[str, bool]:
        """Return status as tuple for backward compatibility."""
        return (self.status.value, self.is_protected)
