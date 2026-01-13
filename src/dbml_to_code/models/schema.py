"""Data models for DBML schema representation."""

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ColumnInfo:
    """Information about a database column."""

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
    """Information about a database table."""

    name: str
    columns: List[ColumnInfo]
    relationships: List[RelationshipInfo] = None
    note: Optional[str] = None

    def __post_init__(self):
        if self.relationships is None:
            self.relationships = []
