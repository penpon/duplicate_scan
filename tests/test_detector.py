"""Tests for DuplicateDetector."""

import pytest
from datetime import datetime
from src.models.file_meta import FileMeta
from src.services.detector import DuplicateDetector


class TestDuplicateDetector:
    """Test cases for DuplicateDetector."""

    def test_find_duplicates_empty_list(self):
        """Test that empty input returns empty list."""
        detector = DuplicateDetector()
        result = detector.find_duplicates([])
        assert result == []

    def test_find_duplicates_single_file(self):
        """Test that single file returns empty list."""
        detector = DuplicateDetector()
        file = FileMeta(path="/test/file1.txt", size=100, modified_time=datetime.now())
        result = detector.find_duplicates([file])
        assert result == []

    def test_find_duplicates_different_sizes(self):
        """Test that files with different sizes are not grouped."""
        detector = DuplicateDetector()
        file1 = FileMeta(path="/test/file1.txt", size=100, modified_time=datetime.now())
        file2 = FileMeta(path="/test/file2.txt", size=200, modified_time=datetime.now())
        result = detector.find_duplicates([file1, file2])
        assert result == []

    def test_find_duplicates_same_size_different_partial_hash(self):
        """Test that files with same size but different partial hashes are not grouped."""
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

    def test_find_duplicates_same_size_and_partial_hash_different_full_hash(self):
        """Test that files with same size and partial hash but different full hashes are not grouped."""
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

    def test_find_duplicates_exact_duplicates(self):
        """Test that exact duplicates are grouped together."""
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
        result = detector.find_duplicates([file1, file2])
        assert len(result) == 1
        assert len(result[0].files) == 2
        assert result[0].total_size == 200

    def test_find_duplicates_multiple_groups(self):
        """Test that multiple duplicate groups are created correctly."""
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

        result = detector.find_duplicates([file1, file2, file3, file4, file5])
        assert len(result) == 2

        # Check first group
        group1 = next(g for g in result if g.total_size == 200)
        assert len(group1.files) == 2

        # Check second group
        group2 = next(g for g in result if g.total_size == 400)
        assert len(group2.files) == 2

    def test_find_duplicates_three_same_files(self):
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
