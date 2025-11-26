"""Duplicate group data model."""

from dataclasses import dataclass

from src.models.file_meta import FileMeta


@dataclass
class DuplicateGroup:
    """Group of duplicate files with their total size."""

    files: list[FileMeta]
    total_size: int
