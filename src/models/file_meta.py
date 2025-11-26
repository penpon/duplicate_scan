"""File metadata data model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileMeta:
    """Metadata for a file including path, size, and hash information."""

    path: str
    size: int
    modified_time: datetime
    partial_hash: str
    full_hash: str
