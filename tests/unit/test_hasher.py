"""Unit tests for Hasher service."""

import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.hasher import Hasher


class TestHasher:
    """Test cases for Hasher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.hasher = Hasher()

    def test_calculate_partial_hash_small_file(self):
        """Test partial hash calculation for small file (< 8KB)."""
        # Given: A small file with known content
        content = b"Hello, World!"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate partial hash
            result = self.hasher.calculate_partial_hash(temp_file_path)

            # Then: Should match SHA256 of entire file (since file is smaller than 8KB)
            expected = hashlib.sha256(content).hexdigest()
            assert result == expected
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_partial_hash_large_file(self):
        """Test partial hash calculation for large file (> 8KB)."""
        # Given: A large file with specific pattern
        content_4kb = b"A" * 4096
        middle_content = b"B" * 4096
        full_content = content_4kb + middle_content + content_4kb

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(full_content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate partial hash
            result = self.hasher.calculate_partial_hash(temp_file_path)

            # Then: Should match SHA256 of first 4KB + last 4KB
            expected_content = content_4kb + content_4kb  # First 4KB + Last 4KB
            expected = hashlib.sha256(expected_content).hexdigest()
            assert result == expected
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_partial_hash_nonexistent_file(self):
        """Test partial hash calculation for nonexistent file."""
        # Given: A nonexistent file path
        nonexistent_path = "/path/to/nonexistent/file.txt"

        # When: Calculate partial hash
        # Then: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.hasher.calculate_partial_hash(nonexistent_path)

    def test_calculate_full_hash_small_file(self):
        """Test full hash calculation for small file."""
        # Given: A small file with known content
        content = b"Hello, World!"
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate full hash
            result = self.hasher.calculate_full_hash(temp_file_path)

            # Then: Should match SHA256 of entire file
            expected = hashlib.sha256(content).hexdigest()
            assert result == expected
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_full_hash_large_file(self):
        """Test full hash calculation for large file."""
        # Given: A large file with specific content
        content = b"X" * 10000  # 10KB file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate full hash
            result = self.hasher.calculate_full_hash(temp_file_path)

            # Then: Should match SHA256 of entire file
            expected = hashlib.sha256(content).hexdigest()
            assert result == expected
        finally:
            Path(temp_file_path).unlink()

    def test_calculate_full_hash_nonexistent_file(self):
        """Test full hash calculation for nonexistent file."""
        # Given: A nonexistent file path
        nonexistent_path = "/path/to/nonexistent/file.txt"

        # When: Calculate full hash
        # Then: Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            self.hasher.calculate_full_hash(nonexistent_path)

    def test_partial_hash_different_from_full_hash_for_large_files(self):
        """Test that partial and full hashes differ for large files with different middle content."""
        # Given: A large file where first and last 4KB are the same but middle is different
        content_4kb = b"A" * 4096
        middle_content = b"B" * 4096
        full_content = content_4kb + middle_content + content_4kb

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(full_content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate both hashes
            partial_hash = self.hasher.calculate_partial_hash(temp_file_path)
            full_hash = self.hasher.calculate_full_hash(temp_file_path)

            # Then: They should be different (because middle content affects full hash)
            assert partial_hash != full_hash
        finally:
            Path(temp_file_path).unlink()

    def test_hash_performance_large_file(self):
        """Test that hash calculation is performant for large files."""
        # Given: A large file (1MB)
        content = b"Performance test data" * 1000  # ~27KB
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # When: Calculate hashes
            import time

            start_time = time.time()
            partial_hash = self.hasher.calculate_partial_hash(temp_file_path)
            partial_time = time.time() - start_time

            start_time = time.time()
            full_hash = self.hasher.calculate_full_hash(temp_file_path)
            full_time = time.time() - start_time

            # Then: Both should complete and return valid hashes
            assert len(partial_hash) == 64  # SHA256 hex length
            assert len(full_hash) == 64  # SHA256 hex length
            assert partial_hash != full_hash  # Should be different for this content

            # Performance sanity check (should complete quickly)
            assert partial_time < 1.0  # Partial hash should be fast
            assert full_time < 2.0  # Full hash should also be reasonable
        finally:
            Path(temp_file_path).unlink()
