"""Duplicate Detector service."""

from typing import List, Dict, Iterable, Callable, TypeVar, Optional
from collections.abc import Hashable
import logging

from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup
from src.services.hasher import Hasher

logger = logging.getLogger(__name__)

K = TypeVar("K", bound=Hashable)


class DuplicateDetector:
    """Service for detecting duplicate files based on size and hash."""

    def find_duplicates(self, files: List[FileMeta]) -> List[DuplicateGroup]:
        """Find duplicate files by grouping them by size and hash.

        Args:
            files: List of file metadata to analyze

        Returns:
            List of duplicate groups containing 2+ files
        """
        if not files:
            return []

        # Step 1: Group by size
        size_groups = self._group_by_key(files, lambda f: f.size)

        # Step 2: Filter groups with 2+ files and group by partial hash
        partial_hash_groups = []
        for files_with_same_size in size_groups.values():
            if len(files_with_same_size) >= 2:
                # Filter out files with no partial_hash
                files_with_partial = [
                    f for f in files_with_same_size if f.partial_hash is not None
                ]
                if len(files_with_partial) >= 2:
                    partial_groups = self._group_by_key(
                        files_with_partial, lambda f: f.partial_hash
                    )
                    # Add groups with 2+ files sharing same partial hash
                    partial_hash_groups.extend(
                        [group for group in partial_groups.values() if len(group) >= 2]
                    )

        # Step 3: Group by full hash to find exact duplicates
        duplicate_groups = []
        for files_with_same_partial in partial_hash_groups:
            # Filter out files with no full_hash
            files_with_full = [
                f for f in files_with_same_partial if f.full_hash is not None
            ]
            if len(files_with_full) >= 2:
                full_hash_groups = self._group_by_key(
                    files_with_full, lambda f: f.full_hash
                )
                # Create duplicate groups for exact matches (2+ files)
                for exact_duplicates in full_hash_groups.values():
                    if len(exact_duplicates) >= 2:
                        duplicate_groups.append(DuplicateGroup(files=exact_duplicates))

        return duplicate_groups

    def find_duplicates_optimized(
        self,
        files: List[FileMeta],
        hasher: Hasher,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[DuplicateGroup]:
        """Find duplicate files using the 5-stage optimized pipeline.

        The pipeline performs:
        1. Size grouping without I/O to find potential duplicates.
        2. Parallel partial hash calculation to remove mismatches early.
        3. Partial hash grouping to narrow candidates further.
        4. Parallel full hash calculation on remaining candidates.
        5. Final grouping by full hash to emit exact duplicates.

        Args:
            files: List of file metadata to analyze.
            hasher: Hasher instance for parallel hash computation.
            progress_callback: Optional callback invoked as
                ``callback(message, processed_items, stage_total)``.

        Returns:
            List of duplicate groups containing 2+ files.

        Raises:
            FileNotFoundError: Propagated from ``Hasher`` when a file no longer exists.
            OSError: Propagated when the underlying filesystem encounters an error.
        """
        if not files:
            if progress_callback:
                progress_callback("No files to process", 0, 0)
            return []

        size_candidates = self._collect_size_candidates(files, progress_callback)
        if not size_candidates:
            if progress_callback:
                progress_callback("No duplicate size candidates found", 0, len(files))
            return []

        partial_candidates = self._collect_partial_candidates(
            size_candidates, hasher, progress_callback
        )
        if not partial_candidates:
            if progress_callback:
                progress_callback(
                    "No partial hash matches found", 0, len(size_candidates)
                )
            return []

        duplicate_groups = self._collect_full_hash_duplicates(
            partial_candidates, hasher, progress_callback
        )
        if progress_callback:
            progress_callback("Completed", len(duplicate_groups), len(files))

        return duplicate_groups

    def _collect_size_candidates(
        self,
        files: List[FileMeta],
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[FileMeta]:
        """Collect files that share the same size.

        Args:
            files: All files in the scan scope.
            progress_callback: Optional callback for reporting progress.

        Returns:
            Files that belong to size buckets with >= 2 members.
        """
        size_groups = self._group_by_key(files, lambda f: f.size)
        size_candidates: List[FileMeta] = []
        for group in size_groups.values():
            if len(group) >= 2:
                size_candidates.extend(group)

        if progress_callback:
            progress_callback("Grouping by size", len(files), len(files))
        return size_candidates

    def _collect_partial_candidates(
        self,
        size_candidates: List[FileMeta],
        hasher: Hasher,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[FileMeta]:
        """Run partial hashes and filter candidates with matching hashes."""
        hasher.calculate_partial_hashes_parallel(size_candidates)
        if progress_callback:
            progress_callback(
                "Computing partial hashes",
                len(size_candidates),
                len(size_candidates),
            )

        files_with_partial = [f for f in size_candidates if f.partial_hash is not None]
        skipped_count = len(size_candidates) - len(files_with_partial)
        if skipped_count > 0:
            logger.warning(
                "Skipped %d files due to partial hash calculation failures",
                skipped_count,
            )
        if progress_callback:
            progress_callback(
                "Grouping by partial hash",
                len(files_with_partial),
                len(size_candidates),
            )

        partial_groups = self._group_by_key(
            files_with_partial, lambda f: f.partial_hash
        )
        partial_candidates: List[FileMeta] = []
        for group in partial_groups.values():
            if len(group) >= 2:
                partial_candidates.extend(group)
        return partial_candidates

    def _collect_full_hash_duplicates(
        self,
        partial_candidates: List[FileMeta],
        hasher: Hasher,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[DuplicateGroup]:
        """Compute full hashes and build DuplicateGroup objects."""
        hasher.calculate_full_hashes_parallel(partial_candidates)
        if progress_callback:
            progress_callback(
                "Computing full hashes",
                len(partial_candidates),
                len(partial_candidates),
            )

        files_with_full = [f for f in partial_candidates if f.full_hash is not None]
        skipped_count = len(partial_candidates) - len(files_with_full)
        if skipped_count > 0:
            logger.warning(
                "Skipped %d files due to full hash calculation failures", skipped_count
            )
        if progress_callback:
            progress_callback(
                "Final grouping",
                len(files_with_full),
                len(partial_candidates),
            )

        full_groups = self._group_by_key(files_with_full, lambda f: f.full_hash)
        duplicate_groups: List[DuplicateGroup] = []
        for exact_duplicates in full_groups.values():
            if len(exact_duplicates) >= 2:
                duplicate_groups.append(DuplicateGroup(files=exact_duplicates))
        return duplicate_groups

    def _group_by_key(
        self, items: Iterable[FileMeta], key_func: Callable[[FileMeta], K]
    ) -> Dict[K, List[FileMeta]]:
        """Group items by a key function.

        Args:
            items: Items to group
            key_func: Function to extract grouping key from item

        Returns:
            Dictionary mapping keys to lists of items
        """
        groups: Dict[K, List[FileMeta]] = {}
        for item in items:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
