"""Deleter service for safely moving files to trash."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from send2trash import send2trash

from ..models.file_meta import FileMeta


@dataclass
class DeleteResult:
    """Result of a delete operation."""

    deleted_files: List[str] = field(default_factory=list)
    failed_files: List[Tuple[str, str]] = field(default_factory=list)
    total_deleted: int = 0
    total_failed: int = 0
    space_saved: int = 0


class Deleter:
    """Service for safely deleting files by moving them to trash."""

    def delete_files(
        self,
        files: List[FileMeta],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> DeleteResult:
        """
        Delete files by moving them to trash.

        Args:
            files: List of files to delete.
            progress_callback: Optional callback for progress updates.
                Receives (file_path, current_index, total_count).

        Returns:
            DeleteResult with details of the operation.
        """
        result = DeleteResult()
        total_count = len(files)

        for index, file_meta in enumerate(files):
            file_path = file_meta.path

            try:
                send2trash(file_path)
                result.deleted_files.append(file_path)
                result.total_deleted += 1
                result.space_saved += file_meta.size
            except (OSError, Exception) as e:
                result.failed_files.append((file_path, str(e)))
                result.total_failed += 1

            if progress_callback:
                progress_callback(file_path, index + 1, total_count)

        return result

    def format_size(self, size_bytes: int) -> str:
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
