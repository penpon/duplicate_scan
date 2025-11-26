"""Duplicate group data model."""

from dataclasses import dataclass
from typing import Union

from .file_meta import FileMeta


@dataclass
class DuplicateGroup:
    """Group of duplicate files with their total size."""

    files: list[FileMeta]
    total_size: Union[int, None] = None

    @property
    def computed_total_size(self) -> int:
        """Calculate total size of all files in the group."""
        return sum(getattr(f, "size", 0) for f in self.files)

    def __post_init__(self):
        """Compute total_size if not provided."""
        if self.total_size is None:
            self.total_size = self.computed_total_size
