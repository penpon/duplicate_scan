"""Hasher service for calculating file hashes.

This service provides optimized hash calculation for large files,
particularly useful for network drives where I/O performance matters.
Uses SHA256 for cryptographic-strength hashing.
"""

import hashlib
from pathlib import Path
from typing import Union


class Hasher:
    """
    Service for calculating file hashes optimized for large files on network drives.

    Features:
    - Partial hashing using first and last 4KB for quick duplicate detection
    - Full hashing for definitive verification
    - Memory-efficient chunked reading for large files
    - Comprehensive error handling

    Attributes:
        chunk_size (int): Size of chunks to read (4KB default for partial hashing)
        read_buffer_size (int): Buffer size for full file hashing (64KB for performance)
    """

    def __init__(self, chunk_size: int = 4096, read_buffer_size: int = 65536) -> None:
        """
        Initialize the hasher service.

        Args:
            chunk_size: Size of chunks for partial hashing in bytes (default: 4KB)
            read_buffer_size: Buffer size for full file hashing in bytes (default: 64KB)
        """
        self.chunk_size = chunk_size
        self.read_buffer_size = read_buffer_size

    def calculate_partial_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate partial hash using first and last 4KB of the file.

        This method is optimized for quick duplicate detection on large files.
        For files smaller than 8KB, calculates hash of the entire file.

        Args:
            file_path: Path to the file to hash

        Returns:
            SHA256 hash as 64-character hexadecimal string

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read due to permissions
            OSError: If there's an I/O error reading the file
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise OSError(f"Path is not a file: {file_path}")

        try:
            file_size = path.stat().st_size
        except OSError as e:
            raise OSError(f"Cannot get file size: {file_path}") from e

        try:
            with open(path, "rb") as file:
                if file_size <= self.chunk_size * 2:  # 8KB or less, hash entire file
                    content = file.read()
                    return hashlib.sha256(content).hexdigest()
                else:
                    # Read first chunk
                    first_chunk = file.read(self.chunk_size)
                    if len(first_chunk) < self.chunk_size:
                        # File was truncated during reading, hash what we got
                        return hashlib.sha256(first_chunk).hexdigest()

                    # Seek to last chunk and read it
                    try:
                        file.seek(-self.chunk_size, 2)
                        last_chunk = file.read(self.chunk_size)
                    except OSError:
                        # If seeking fails (can happen with some network files),
                        # fall back to full hash
                        file.seek(0)
                        hash_sha256 = hashlib.sha256()
                        while chunk := file.read(self.read_buffer_size):
                            hash_sha256.update(chunk)
                        return hash_sha256.hexdigest()

                    # Hash first + last chunks
                    combined_content = first_chunk + last_chunk
                    return hashlib.sha256(combined_content).hexdigest()
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading file: {file_path}") from e
        except OSError as e:
            raise OSError(f"I/O error reading file: {file_path}") from e

    def calculate_full_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate full hash of the entire file.

        Uses chunked reading to handle large files efficiently without
        loading the entire file into memory.

        Args:
            file_path: Path to the file to hash

        Returns:
            SHA256 hash as 64-character hexadecimal string

        Raises:
            FileNotFoundError: If the file does not exist
            PermissionError: If the file cannot be read due to permissions
            OSError: If there's an I/O error reading the file
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise OSError(f"Path is not a file: {file_path}")

        hash_sha256 = hashlib.sha256()

        try:
            with open(path, "rb") as file:
                while chunk := file.read(self.read_buffer_size):
                    hash_sha256.update(chunk)
        except PermissionError as e:
            raise PermissionError(f"Permission denied reading file: {file_path}") from e
        except OSError as e:
            raise OSError(f"I/O error reading file: {file_path}") from e

        return hash_sha256.hexdigest()
