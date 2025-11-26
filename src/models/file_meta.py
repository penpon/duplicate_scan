"""File metadata data model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class FileMeta:
    """Metadata for a file including path, size, and hash information."""

    path: str
    size: int
    modified_time: datetime
    partial_hash: Optional[str] = None
    full_hash: Optional[str] = None

    def __hash__(self) -> int:
        """Make FileMeta hashable for use in sets."""
        return hash((self.path, self.size, self.modified_time))

    def __eq__(self, other: object) -> bool:
        """Ensure equality aligns with hashing fields."""
        if not isinstance(other, FileMeta):
            return NotImplemented
        return (
            self.path,
            self.size,
            self.modified_time,
        ) == (
            other.path,
            other.size,
            other.modified_time,
        )
