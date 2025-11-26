"""Tests for data models."""

from datetime import datetime
from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup


def test_file_meta_creation():
    """Test FileMeta dataclass creation."""
    now = datetime.now()
    file_meta = FileMeta(
        path="/test/file.txt",
        size=1024,
        modified_time=now,
        partial_hash="abc123",
        full_hash="def456",
    )

    assert file_meta.path == "/test/file.txt"
    assert file_meta.size == 1024
    assert file_meta.modified_time == now
    assert file_meta.partial_hash == "abc123"
    assert file_meta.full_hash == "def456"


def test_duplicate_group_creation():
    """Test DuplicateGroup dataclass creation."""
    now = datetime.now()
    file1 = FileMeta(
        path="/test/file1.txt",
        size=1024,
        modified_time=now,
        partial_hash="abc123",
        full_hash="def456",
    )
    file2 = FileMeta(
        path="/test/file2.txt",
        size=1024,
        modified_time=now,
        partial_hash="abc123",
        full_hash="def456",
    )

    duplicate_group = DuplicateGroup(files=[file1, file2], total_size=2048)

    assert len(duplicate_group.files) == 2
    assert duplicate_group.total_size == 2048
    assert duplicate_group.files[0].path == "/test/file1.txt"
    assert duplicate_group.files[1].path == "/test/file2.txt"
