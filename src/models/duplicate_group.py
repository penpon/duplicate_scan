"""Duplicate group data model."""

from dataclasses import dataclass
from typing import List

from .file_meta import FileMeta


@dataclass
class DuplicateGroup:
    """Group of duplicate files with their total size."""

    files: List[FileMeta]
    total_size: int
