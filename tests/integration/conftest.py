"""Shared fixtures and helpers for integration tests."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Generator

import pytest

from src.models.file_meta import FileMeta
from src.services.deleter import Deleter
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def hasher() -> Hasher:
    """Create a Hasher instance."""
    return Hasher()


@pytest.fixture
def detector() -> DuplicateDetector:
    """Create a DuplicateDetector instance."""
    return DuplicateDetector()


@pytest.fixture
def deleter(temp_dir: Path) -> Deleter:
    """Create a Deleter instance with temp_dir as backup base."""
    return Deleter(backup_base_dir=temp_dir)


@pytest.fixture
def _create_test_file() -> Callable[[Path, bytes], FileMeta]:
    """Return helper for creating a test file and its FileMeta."""

    def _create(path: Path, content: bytes) -> FileMeta:
        path.write_bytes(content)
        stat = path.stat()
        return FileMeta(
            path=str(path),
            size=stat.st_size,
            modified_time=datetime.fromtimestamp(stat.st_mtime),
        )

    return _create
