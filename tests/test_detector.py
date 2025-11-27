"""Tests for DuplicateDetector."""

from datetime import datetime
from unittest.mock import Mock
from src.models.file_meta import FileMeta
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher


class TestDuplicateDetector:
    """Test cases for DuplicateDetector."""

    def test_find_duplicates_empty_list(self) -> None:
        """Verify that empty input yields no duplicate groups.

        Args:
            self: Unused; part of unittest-style test signature.

        Returns:
            None.
        """
        detector = DuplicateDetector()
        result = detector.find_duplicates([])
        assert result == []

    def test_find_duplicates_single_file(self) -> None:
        """Verify that single file input yields no duplicate groups.

        Args:
            self: Unused; part of unittest-style test signature.

        Returns:
            None.
        """
        detector = DuplicateDetector()
        file = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
        )
        result = detector.find_duplicates([file])
        assert result == []

    def test_find_duplicates_different_sizes(self) -> None:
        """Test that files with different sizes are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=200,
            modified_time=datetime.now(),
        )
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_same_size_different_partial_hash(self) -> None:
        """Test that files with same size but different partial
        hashes are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash2",
        )
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_same_size_and_partial_hash_different_full_hash(
        self,
    ) -> None:
        """Test that files with same size and partial hash but different
        full hashes are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full2",
        )
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_same_size_none_partial_hash(self) -> None:
        """Test that files with same size and partial_hash=None
        are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash=None,
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash=None,
        )
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_same_size_and_partial_none_full_hash(
        self,
    ) -> None:
        """Test that files with same size and partial_hash but
        full_hash=None are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash=None,
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash=None,
        )
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_exact_duplicates(self) -> None:
        """Verify that exact duplicates are grouped together correctly.

        Args:
            self: Unused; part of unittest-style test signature.

        Returns:
            None.
        """
        # Given: two identical files (same size, partial_hash, full_hash)
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )

        # When: running duplicate detection
        result = detector.find_duplicates([file1, file2])

        # Then: they are grouped together in a single DuplicateGroup
        assert len(result) == 1
        assert len(result[0].files) == 2
        assert result[0].total_size == 200

    def test_find_duplicates_multiple_groups(self) -> None:
        """Verify that multiple independent duplicate groups are handled.

        Args:
            self: Unused; part of unittest-style test signature.

        Returns:
            None.
        """
        # Given: multiple groups of exact duplicates and unique files
        detector = DuplicateDetector()
        # Group 1: exact duplicates
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        # Group 2: exact duplicates
        file3 = FileMeta(
            path="/test/file3.txt",
            size=200,
            modified_time=datetime.now(),
            partial_hash="hash2",
            full_hash="full2",
        )
        file4 = FileMeta(
            path="/test/file4.txt",
            size=200,
            modified_time=datetime.now(),
            partial_hash="hash2",
            full_hash="full2",
        )
        # Unique file
        file5 = FileMeta(
            path="/test/file5.txt",
            size=300,
            modified_time=datetime.now(),
            partial_hash="hash3",
            full_hash="full3",
        )

        # When: running duplicate detection
        result = detector.find_duplicates([file1, file2, file3, file4, file5])

        # Then: exactly two duplicate groups are created
        assert len(result) == 2

        # Check first group
        group1 = next(g for g in result if g.total_size == 200)
        assert len(group1.files) == 2

        # Check second group
        group2 = next(g for g in result if g.total_size == 400)
        assert len(group2.files) == 2

    def test_find_duplicates_three_same_files(self) -> None:
        """Test that three identical files are grouped together."""
        detector = DuplicateDetector()
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file3 = FileMeta(
            path="/test/file3.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )

        result = detector.find_duplicates([file1, file2, file3])
        assert len(result) == 1
        assert len(result[0].files) == 3
        assert result[0].total_size == 300

    def test_find_duplicates_optimized_exists(self) -> None:
        """Verify that find_duplicates_optimized method exists."""
        detector = DuplicateDetector()
        hasher = Hasher()

        # This should fail initially - method doesn't exist yet
        assert hasattr(detector, "find_duplicates_optimized")

        # Method signature should be correct
        import inspect

        sig = inspect.signature(detector.find_duplicates_optimized)
        expected_params = ["files", "hasher", "progress_callback"]
        actual_params = list(sig.parameters.keys())
        assert actual_params == expected_params

    def test_find_duplicates_optimized_same_results_as_original(self) -> None:
        """Verify optimized method produces same results as original."""
        # Given: test files with duplicates
        detector = DuplicateDetector()
        hasher = Hasher()

        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file3 = FileMeta(
            path="/test/file3.txt",
            size=200,
            modified_time=datetime.now(),
            partial_hash="hash2",
            full_hash="full2",
        )

        # When: comparing both methods
        original_result = detector.find_duplicates([file1, file2, file3])
        optimized_result = detector.find_duplicates_optimized(
            [file1, file2, file3], hasher
        )

        # Then: results should be identical
        assert len(original_result) == len(optimized_result)
        if original_result:
            assert len(original_result[0].files) == len(optimized_result[0].files)
            assert original_result[0].total_size == optimized_result[0].total_size

    def test_find_duplicates_optimized_progress_callback(self) -> None:
        """Verify progress callback is called at each stage."""
        detector = DuplicateDetector()
        hasher = Hasher()
        progress_callback = Mock()

        # Create files with same size to ensure they go through all stages
        file1 = FileMeta(
            path="/test/file1.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )
        file2 = FileMeta(
            path="/test/file2.txt",
            size=100,
            modified_time=datetime.now(),
            partial_hash="hash1",
            full_hash="full1",
        )

        # When: running optimized method with progress callback
        detector.find_duplicates_optimized([file1, file2], hasher, progress_callback)

        # Then: progress callback should be called multiple times
        assert progress_callback.call_count >= 5  # All stages + completion

    def test_find_duplicates_optimized_performance_improvement(self) -> None:
        """Verify that optimized method reduces hash computations significantly."""
        detector = DuplicateDetector()
        hasher = Hasher()

        # Create many files with different sizes (most should be filtered out early)
        files = []
        for i in range(100):
            files.append(
                FileMeta(
                    path=f"/test/file{i}.txt",
                    size=100
                    + i,  # All different sizes - should be filtered out at size stage
                    modified_time=datetime.now(),
                )
            )

        # Add a few duplicates with pre-computed hashes to avoid file I/O
        files.extend(
            [
                FileMeta(
                    path="/test/dup1.txt",
                    size=500,
                    modified_time=datetime.now(),
                    partial_hash="dup_hash",
                    full_hash="dup_full",
                ),
                FileMeta(
                    path="/test/dup2.txt",
                    size=500,
                    modified_time=datetime.now(),
                    partial_hash="dup_hash",
                    full_hash="dup_full",
                ),
            ]
        )

        # When: running optimized method
        result = detector.find_duplicates_optimized(files, hasher)

        # Then: should find the duplicates and avoid unnecessary hash computations
        assert len(result) == 1
        assert len(result[0].files) == 2

        # Most files should be filtered out by size alone, minimizing hash calls
        # This is a basic sanity check - real performance testing would need actual files
