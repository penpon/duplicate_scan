"""Duplicate Detector service."""

from typing import List, Dict, Iterable

from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup


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
                partial_groups = self._group_by_key(
                    files_with_same_size, lambda f: f.partial_hash or ""
                )
                # Add groups with 2+ files sharing same partial hash
                partial_hash_groups.extend(
                    [group for group in partial_groups.values() if len(group) >= 2]
                )

        # Step 3: Group by full hash to find exact duplicates
        duplicate_groups = []
        for files_with_same_partial in partial_hash_groups:
            full_hash_groups = self._group_by_key(
                files_with_same_partial, lambda f: f.full_hash or ""
            )
            # Create duplicate groups for exact matches (2+ files)
            for exact_duplicates in full_hash_groups.values():
                if len(exact_duplicates) >= 2:
                    duplicate_groups.append(DuplicateGroup(files=exact_duplicates))

        return duplicate_groups

    def _group_by_key(
        self, items: Iterable[FileMeta], key_func
    ) -> Dict[str, List[FileMeta]]:
        """Group items by a key function.

        Args:
            items: Items to group
            key_func: Function to extract grouping key from item

        Returns:
            Dictionary mapping keys to lists of items
        """
        groups: Dict[str, List[FileMeta]] = {}
        for item in items:
            key = key_func(item)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        return groups
