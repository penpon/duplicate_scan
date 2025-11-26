"""Duplicate group data model."""

from dataclasses import dataclass

from .file_meta import FileMeta


@dataclass
class DuplicateGroup:
    """Group of duplicate files with their total size."""

    files: list[FileMeta]

    @property
    def total_size(self) -> int:
        """Calculate total size from all files."""
        return sum(file.size for file in self.files)
