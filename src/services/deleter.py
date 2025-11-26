"""Deleter service for safely moving files to a backup directory."""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from ..models.file_meta import FileMeta


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted_files: List[str] = field(default_factory=list)
    failed_files: List[Tuple[str, str]] = field(default_factory=list)
    total_deleted: int = 0
    total_failed: int = 0
    space_saved: int = 0
    backup_directory: Optional[str] = None


class Deleter:
    """Service for safely deleting files by moving to a backup directory."""

    def __init__(self, backup_base_dir: Optional[Path] = None) -> None:
        """
        Initialize Deleter.

        Args:
            backup_base_dir: Base directory for backup folders.
                Defaults to current working directory.
        """
        self.backup_base_dir = backup_base_dir or Path.cwd()

    def _create_backup_directory(self) -> Path:
        """
        Create a timestamped backup directory.

        Returns:
            Path to the created backup directory.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base_dir / f"deleted_files_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def _get_unique_filename(self, backup_dir: Path, original_path: Path) -> Path:
        """
        Get a unique filename in the backup directory.

        Args:
            backup_dir: The backup directory.
            original_path: Original file path.

        Returns:
            Unique path in the backup directory.
        """
        dest_path = backup_dir / original_path.name
        if not dest_path.exists():
            return dest_path

        # Handle filename conflicts by adding a counter
        counter = 1
        stem = original_path.stem
        suffix = original_path.suffix
        while dest_path.exists():
            dest_path = backup_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        return dest_path

    def delete_files(
        self,
        files: List[FileMeta],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> DeleteResult:
        """
        Delete files by moving them to a backup directory.

        Args:
            files: List of files to delete.
            progress_callback: Optional callback for progress updates.
                Receives (file_path, current_index, total_count).

        Returns:
            DeleteResult with details of the operation.
        """
        result = DeleteResult()
        total_count = len(files)

        if not files:
            return result

        # Create backup directory
        backup_dir = self._create_backup_directory()
        result.backup_directory = str(backup_dir)

        for index, file_meta in enumerate(files):
            file_path = Path(file_meta.path)

            try:
                dest_path = self._get_unique_filename(backup_dir, file_path)
                shutil.move(str(file_path), str(dest_path))
                result.deleted_files.append(str(file_path))
                result.total_deleted += 1
                result.space_saved += file_meta.size
            except Exception as e:
                result.failed_files.append((str(file_path), str(e)))
                result.total_failed += 1

            if progress_callback:
                progress_callback(str(file_path), index + 1, total_count)

        return result

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """
        Format file size to human-readable string.

        Args:
            size_bytes: Size in bytes.

        Returns:
            Formatted size string (e.g., "1.5 MB").
        """
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} B"
