"""Integration tests for the complete duplicate detection workflow.

Tests the integration of Hasher, Detector, and Deleter services
to verify the entire application flow works correctly.
"""

from datetime import datetime
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from src.models.file_meta import FileMeta
from src.services.deleter import Deleter
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher


class TestHasherDetectorIntegration:
    """Integration tests for Hasher and Detector services."""

    def test_detect_duplicates_with_real_files(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test duplicate detection with actual files on disk.

        Given: Multiple files with some duplicates
        When: Hashing and detecting duplicates
        Then: Correct duplicate groups are identified
        """
        # Given: Create test files - 2 duplicates and 1 unique
        content_a = b"This is duplicate content A" * 100
        content_b = b"This is unique content B" * 100

        file1 = _create_test_file(temp_dir / "file1.txt", content_a)
        file2 = _create_test_file(temp_dir / "file2.txt", content_a)
        # duplicate of file1
        file3 = _create_test_file(temp_dir / "file3.txt", content_b)  # unique

        # When: Calculate hashes for all files
        files = [file1, file2, file3]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: Detect duplicates
        duplicates = detector.find_duplicates(files)

        # Verify: One duplicate group with 2 files
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 2
        paths = {f.path for f in duplicates[0].files}
        assert str(temp_dir / "file1.txt") in paths, "file1 should be in group"
        assert str(temp_dir / "file2.txt") in paths, "file2 should be in group"

    def test_detect_multiple_duplicate_groups(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test detection of multiple independent duplicate groups.

        Given: Files forming multiple duplicate groups
        When: Hashing and detecting duplicates
        Then: All duplicate groups are correctly identified
        """
        # Given: Create multiple duplicate groups
        content_a = b"Group A content" * 100
        content_b = b"Group B content" * 100
        content_c = b"Unique content" * 100

        # Group A: 2 duplicates
        file_a1 = _create_test_file(temp_dir / "a1.txt", content_a)
        file_a2 = _create_test_file(temp_dir / "a2.txt", content_a)

        # Group B: 3 duplicates
        file_b1 = _create_test_file(temp_dir / "b1.txt", content_b)
        file_b2 = _create_test_file(temp_dir / "b2.txt", content_b)
        file_b3 = _create_test_file(temp_dir / "b3.txt", content_b)

        # Unique file
        file_c = _create_test_file(temp_dir / "c.txt", content_c)

        # When: Hash all files
        files = [file_a1, file_a2, file_b1, file_b2, file_b3, file_c]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: Detect duplicates
        duplicates = detector.find_duplicates(files)

        # Verify: Two duplicate groups
        assert len(duplicates) == 2

        # Find groups by size
        group_sizes = sorted([len(g.files) for g in duplicates])
        assert group_sizes == [2, 3]

    def test_no_duplicates_with_different_content(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test that files with different content are not grouped.

        Given: Files with unique content
        When: Hashing and detecting duplicates
        Then: No duplicate groups are found
        """
        # Given: Create files with unique content
        file1 = _create_test_file(temp_dir / "file1.txt", b"Content 1" * 100)
        file2 = _create_test_file(temp_dir / "file2.txt", b"Content 2" * 100)
        file3 = _create_test_file(temp_dir / "file3.txt", b"Content 3" * 100)

        # When: Hash all files
        files = [file1, file2, file3]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: No duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 0

    def test_same_size_different_content(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test files with same size but different content.

        Given: Files with same size but different content
        When: Hashing and detecting duplicates
        Then: No duplicate groups are found
        """
        # Given: Create files with same size but different content
        content1 = b"A" * 1000
        content2 = b"B" * 1000
        content3 = b"C" * 1000

        file1 = _create_test_file(temp_dir / "file1.txt", content1)
        file2 = _create_test_file(temp_dir / "file2.txt", content2)
        file3 = _create_test_file(temp_dir / "file3.txt", content3)

        # Verify same size
        assert file1.size == file2.size == file3.size

        # When: Hash all files
        files = [file1, file2, file3]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: No duplicates (different hashes)
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 0


class TestFullWorkflowIntegration:
    """Integration tests for the complete workflow including deletion."""

    def test_complete_workflow_scan_detect_delete(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        deleter: Deleter,
        _create_test_file,
    ) -> None:
        """Test the complete workflow from scanning to deletion.

        Given: Directory with duplicate files
        When: Scanning, detecting, and deleting duplicates
        Then: Duplicates are correctly identified and deleted
        """
        # Given: Create duplicate files
        content = b"Duplicate content for deletion test" * 100

        original = _create_test_file(temp_dir / "original.txt", content)
        duplicate1 = _create_test_file(temp_dir / "duplicate1.txt", content)
        duplicate2 = _create_test_file(temp_dir / "duplicate2.txt", content)

        # When: Hash files
        files = [original, duplicate1, duplicate2]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Detect duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 3

        # Select files to delete (keep original, delete duplicates)
        files_to_delete = [f for f in duplicates[0].files if "duplicate" in f.path]
        assert len(files_to_delete) == 2

        # Delete with mocked send2trash
        with patch("src.services.deleter.send2trash") as mock_trash:
            result = deleter.delete_files(files_to_delete)

            # Then: Verify deletion results
            assert result.total_deleted == 2
            assert result.total_failed == 0
            assert len(result.deleted_files) == 2
            assert mock_trash.call_count == 2

    def test_workflow_with_progress_callback(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        deleter: Deleter,
        _create_test_file,
    ) -> None:
        """Test workflow with progress callback during deletion.

        Given: Duplicate files and a progress callback
        When: Deleting files
        Then: Progress callback is called for each file
        """
        # Given: Create duplicate files
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        # Hash files
        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Detect duplicates
        duplicates = detector.find_duplicates([file1, file2])
        assert len(duplicates) == 1

        # Setup progress callback
        progress_calls: List[tuple] = []

        def progress_callback(path: str, current: int, total: int) -> None:
            progress_calls.append((path, current, total))

        # When: Delete with progress callback
        files_to_delete = [duplicates[0].files[0]]  # Delete one file

        with patch("src.services.deleter.send2trash"):
            deleter.delete_files(
                files_to_delete,
                progress_callback=progress_callback,
            )

        # Then: Progress callback was called
        assert len(progress_calls) == 1
        assert progress_calls[0][1] == 1  # current
        assert progress_calls[0][2] == 1  # total

    def test_workflow_handles_deletion_errors(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        deleter: Deleter,
        _create_test_file,
    ) -> None:
        """Test workflow handles deletion errors gracefully.

        Given: Files where some deletions will fail
        When: Attempting to delete files
        Then: Errors are recorded and other files are still processed
        """
        # Given: Create files
        content = b"Test content" * 100
        file1 = _create_test_file(temp_dir / "file1.txt", content)
        file2 = _create_test_file(temp_dir / "file2.txt", content)

        # Hash files
        for f in [file1, file2]:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Detect duplicates
        duplicates = detector.find_duplicates([file1, file2])
        files_to_delete = duplicates[0].files

        # When: Delete with one failure
        def mock_send2trash(path: str) -> None:
            if "file1" in path:
                raise PermissionError("File in use")

        with patch(
            "src.services.deleter.send2trash",
            side_effect=mock_send2trash,
        ):
            result = deleter.delete_files(files_to_delete)

        # Then: One success, one failure
        assert result.total_deleted == 1
        assert result.total_failed == 1
        assert len(result.failed_files) == 1
        assert "file1" in result.failed_files[0][0]


class TestLargeFileHandling:
    """Integration tests for handling large files efficiently."""

    def test_large_file_partial_hash_optimization(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test that partial hashing correctly identifies
        large file duplicates.

        Given: Large files (>8KB) with same content
        When: Using partial hash for initial filtering
        Then: Duplicates are correctly identified
        """
        # Given: Create large duplicate files (16KB each)
        # 16KB = 4KB + 8KB + 4KB
        large_content = b"A" * 4096 + b"B" * 8192 + b"C" * 4096

        file1 = _create_test_file(temp_dir / "large1.bin", large_content)
        # duplicate of file1
        file2 = _create_test_file(temp_dir / "large2.bin", large_content)

        # When: Hash files
        files = [file1, file2]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Verify partial hashes match
        assert file1.partial_hash == file2.partial_hash

        # Then: Detect duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 2

    def test_large_files_same_partial_different_full(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test files with same partial hash but different full hash.

        Given: Large files with same start/end but different middle
        When: Hashing and detecting
        Then: Files are not grouped as duplicates
        """
        # Given: Files with same first/last 4KB but different middle
        start = b"S" * 4096
        end = b"E" * 4096
        middle1 = b"M" * 8192
        middle2 = b"N" * 8192

        content1 = start + middle1 + end
        content2 = start + middle2 + end

        file1 = _create_test_file(temp_dir / "file1.bin", content1)
        file2 = _create_test_file(temp_dir / "file2.bin", content2)

        # When: Hash files
        files = [file1, file2]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Partial hashes should match (same start/end)
        assert file1.partial_hash == file2.partial_hash
        # Full hashes should differ
        assert file1.full_hash != file2.full_hash

        # Then: No duplicates (different full hash)
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 0


class TestEdgeCases:
    """Integration tests for edge cases and error handling."""

    def test_empty_file_duplicates(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test detection of duplicate empty files.

        Given: Multiple empty files
        When: Hashing and detecting
        Then: Empty files are grouped as duplicates
        """
        # Given: Create empty files
        file1 = _create_test_file(temp_dir / "empty1.txt", b"")
        file2 = _create_test_file(temp_dir / "empty2.txt", b"")

        # When: Hash files
        files = [file1, file2]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: Empty files are duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 2

    def test_single_byte_files(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test detection of single-byte file duplicates.

        Given: Multiple single-byte files with same content
        When: Hashing and detecting
        Then: Files are correctly identified as duplicates
        """
        # Given: Create single-byte files
        file1 = _create_test_file(temp_dir / "byte1.txt", b"X")
        file2 = _create_test_file(temp_dir / "byte2.txt", b"X")
        file3 = _create_test_file(temp_dir / "byte3.txt", b"Y")  # different

        # When: Hash files
        files = [file1, file2, file3]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: Only matching files are duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 2

    def test_file_not_found_during_hash(
        self,
        temp_dir: Path,
        hasher: Hasher,
    ) -> None:
        """Test handling of missing files during hashing.

        Given: A FileMeta pointing to a non-existent file
        When: Attempting to hash
        Then: FileNotFoundError is raised
        """
        # Given: FileMeta for non-existent file
        file_meta = FileMeta(
            path=str(temp_dir / "nonexistent.txt"),
            size=100,
            modified_time=datetime.now(),
        )

        # When/Then: Hashing raises FileNotFoundError
        with pytest.raises(FileNotFoundError):
            hasher.calculate_partial_hash(file_meta.path)

        with pytest.raises(FileNotFoundError):
            hasher.calculate_full_hash(file_meta.path)

    def test_mixed_file_sizes(
        self,
        temp_dir: Path,
        hasher: Hasher,
        detector: DuplicateDetector,
        _create_test_file,
    ) -> None:
        """Test detection with mixed file sizes.

        Given: Files of various sizes with some duplicates
        When: Hashing and detecting
        Then: Only same-size duplicates are grouped
        """
        # Given: Create files of different sizes
        small_content = b"small"
        medium_content = b"medium content here"
        large_content = b"large content " * 100

        # Small duplicates
        small1 = _create_test_file(temp_dir / "small1.txt", small_content)
        small2 = _create_test_file(temp_dir / "small2.txt", small_content)

        # Medium unique
        medium = _create_test_file(temp_dir / "medium.txt", medium_content)

        # Large unique
        large = _create_test_file(temp_dir / "large.txt", large_content)

        # When: Hash all files
        files = [small1, small2, medium, large]
        for f in files:
            f.partial_hash = hasher.calculate_partial_hash(f.path)
            f.full_hash = hasher.calculate_full_hash(f.path)

        # Then: Only small files are duplicates
        duplicates = detector.find_duplicates(files)
        assert len(duplicates) == 1
        assert len(duplicates[0].files) == 2
        assert all("small" in f.path for f in duplicates[0].files)
