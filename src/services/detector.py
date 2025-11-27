"""Duplicate Detector service."""

from typing import List, Dict, Iterable, Callable, TypeVar, Optional
from collections.abc import Hashable

from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup
from src.services.hasher import Hasher

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
        """Find duplicate files using optimized pipeline.

        Args:
            files: List of file metadata to analyze
            hasher: Hasher instance for parallel hash computation
            progress_callback: Optional callback for progress updates

        Returns:
            List of duplicate groups containing 2+ files
        """
        if not files:
            if progress_callback:
                progress_callback("No files to process", 0, 0)
            return []

        # Step 1: Group by size (no I/O)
        if progress_callback:
            progress_callback("Grouping by size", 0, len(files))
        size_groups = self._group_by_key(files, lambda f: f.size)

        # Filter groups with 2+ files
        size_candidates = []
        for size, files_with_same_size in size_groups.items():
            if len(files_with_same_size) >= 2:
                size_candidates.extend(files_with_same_size)

        if not size_candidates:
            if progress_callback:
                progress_callback("No duplicate size candidates found", 0, len(files))
            return []

        # Step 2: Compute partial_hash for candidates (parallel)
        if progress_callback:
            progress_callback("Computing partial hashes", 0, len(size_candidates))
        hasher.calculate_partial_hashes_parallel(size_candidates)

        # Step 3: Group by partial_hash, filter <2
        if progress_callback:
            progress_callback("Grouping by partial hash", 0, len(size_candidates))
        partial_groups = self._group_by_key(
            [f for f in size_candidates if f.partial_hash is not None],
            lambda f: f.partial_hash,
        )

        partial_candidates = []
        for partial_hash, files_with_same_partial in partial_groups.items():
            if len(files_with_same_partial) >= 2:
                partial_candidates.extend(files_with_same_partial)

        if not partial_candidates:
            if progress_callback:
                progress_callback(
                    "No partial hash matches found", 0, len(size_candidates)
                )
            return []

        # Step 4: Compute full_hash for matches (parallel)
        if progress_callback:
            progress_callback("Computing full hashes", 0, len(partial_candidates))
        hasher.calculate_full_hashes_parallel(partial_candidates)

        # Step 5: Final grouping by full_hash
        if progress_callback:
            progress_callback("Final grouping", 0, len(partial_candidates))
        full_groups = self._group_by_key(
            [f for f in partial_candidates if f.full_hash is not None],
            lambda f: f.full_hash,
        )

        # Create duplicate groups for exact matches
        duplicate_groups = []
        for full_hash, exact_duplicates in full_groups.items():
            if len(exact_duplicates) >= 2:
                duplicate_groups.append(DuplicateGroup(files=exact_duplicates))

        if progress_callback:
            progress_callback("Completed", len(duplicate_groups), len(files))

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
