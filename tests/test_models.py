"""Tests for data models."""

from datetime import datetime
from src.models.file_meta import FileMeta
from src.models.duplicate_group import DuplicateGroup


def test_file_meta_creation():
    """Test FileMeta dataclass creation."""
    # Given: Current timestamp and file metadata
    now = datetime.now()

    # When: Creating a FileMeta instance
    file_meta = FileMeta(
        path="/test/file.txt",
        size=1024,
        modified_time=now,
        partial_hash="abc123",
        full_hash="def456",
    )

    # Then: All fields should be correctly set
    assert file_meta.path == "/test/file.txt"
    assert file_meta.size == 1024
    assert file_meta.modified_time == now
    assert file_meta.partial_hash == "abc123"
    assert file_meta.full_hash == "def456"


def test_duplicate_group_creation():
    """Test DuplicateGroup dataclass creation."""
    # Given: Two duplicate files with same hash
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

    # When: Creating a duplicate group
    duplicate_group = DuplicateGroup(files=[file1, file2], total_size=2048)

    # Then: Group should contain both files with correct total size
    assert len(duplicate_group.files) == 2
    assert duplicate_group.total_size == 2048
    assert duplicate_group.files[0].path == "/test/file1.txt"
    assert duplicate_group.files[1].path == "/test/file2.txt"


def test_duplicate_group_empty_files():
    """Test DuplicateGroup with empty files list."""
    # Given: Empty files list
    # When: Creating a duplicate group with empty files
    duplicate_group = DuplicateGroup(files=[], total_size=0)

    # Then: Group should be empty with zero total size
    assert len(duplicate_group.files) == 0
    assert duplicate_group.total_size == 0


def test_duplicate_group_negative_size():
    """Test DuplicateGroup with negative total size."""
    # Given: Single file and negative total size (edge case)
    now = datetime.now()
    file = FileMeta(
        path="/test/file.txt",
        size=1024,
        modified_time=now,
        partial_hash="abc123",
        full_hash="def456",
    )

    # When: Creating a duplicate group with negative total size
    duplicate_group = DuplicateGroup(files=[file], total_size=-100)

    # Then: Group should contain file but with negative total size
    assert len(duplicate_group.files) == 1
    assert duplicate_group.total_size == -100


def test_duplicate_group_single_file():
    """Test DuplicateGroup with single file."""
    # Given: Single file
    now = datetime.now()
    file = FileMeta(
        path="/test/single.txt",
        size=512,
        modified_time=now,
        partial_hash="xyz789",
        full_hash="uvw456",
    )

    # When: Creating a duplicate group with single file
    duplicate_group = DuplicateGroup(files=[file], total_size=512)

    # Then: Group should contain the single file
    assert len(duplicate_group.files) == 1
    assert duplicate_group.total_size == 512
    assert duplicate_group.files[0].path == "/test/single.txt"
