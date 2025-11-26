"""Tests for data models."""

from datetime import datetime
from typing import List

from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup


class TestFileMeta:
    """Test FileMeta dataclass."""

    def test_file_meta_creation(self):
        """Test FileMeta can be created with all fields."""
        # Given
        path = "/path/to/file.txt"
        size = 1024
        modified_time = datetime.now()
        partial_hash = "abc123"
        full_hash = "def456"

        # When
        file_meta = FileMeta(
            path=path,
            size=size,
            modified_time=modified_time,
            partial_hash=partial_hash,
            full_hash=full_hash,
        )

        # Then
        assert file_meta.path == path
        assert file_meta.size == size
        assert file_meta.modified_time == modified_time
        assert file_meta.partial_hash == partial_hash
        assert file_meta.full_hash == full_hash

    def test_file_meta_type_checking(self):
        """Test FileMeta passes type checking."""
        # Given
        file_meta = FileMeta(
            path="/path/to/file.txt",
            size=1024,
            modified_time=datetime.now(),
            partial_hash="abc123",
            full_hash="def456",
        )

        # When & Then
        assert isinstance(file_meta.path, str)
        assert isinstance(file_meta.size, int)
        assert isinstance(file_meta.modified_time, datetime)
        assert isinstance(file_meta.partial_hash, str)
        assert isinstance(file_meta.full_hash, str)


class TestDuplicateGroup:
    """Test DuplicateGroup dataclass."""

    def test_duplicate_group_creation(self):
        """Test DuplicateGroup can be created with files and total_size."""
        # Given
        file1 = FileMeta(
            path="/path/to/file1.txt",
            size=1024,
            modified_time=datetime.now(),
            partial_hash="abc123",
            full_hash="def456",
        )
        file2 = FileMeta(
            path="/path/to/file2.txt",
            size=1024,
            modified_time=datetime.now(),
            partial_hash="abc123",
            full_hash="def456",
        )
        files: List[FileMeta] = [file1, file2]
        total_size = 2048

        # When
        duplicate_group = DuplicateGroup(files=files, total_size=total_size)

        # Then
        assert duplicate_group.files == files
        assert duplicate_group.total_size == total_size
        assert len(duplicate_group.files) == 2

    def test_duplicate_group_type_checking(self):
        """Test DuplicateGroup passes type checking."""
        # Given
        file_meta = FileMeta(
            path="/path/to/file.txt",
            size=1024,
            modified_time=datetime.now(),
            partial_hash="abc123",
            full_hash="def456",
        )
        duplicate_group = DuplicateGroup(files=[file_meta], total_size=1024)

        # When & Then
        assert isinstance(duplicate_group.files, list)
        assert isinstance(duplicate_group.total_size, int)
        assert len(duplicate_group.files) == 1
        assert isinstance(duplicate_group.files[0], FileMeta)
