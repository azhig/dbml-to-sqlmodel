"""Data models for DBML schema representation."""

from dataclasses import dataclass
from typing import Any


@dataclass
class ColumnInfo:
    """Information about a database column."""

    name: str
    type: str
    primary_key: bool
    unique: bool
    nullable: bool
    default: Any = None
    references: list | None = None
    note: str | None = None


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
    columns: list[ColumnInfo]
    relationships: list[RelationshipInfo] | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if self.relationships is None:
            self.relationships = []
