"""Scan configuration data model."""

from dataclasses import dataclass
from typing import Literal

# Constants for validation
MIN_CHUNK_SIZE = 4096
MIN_PARALLEL_WORKERS = 1
MAX_PARALLEL_WORKERS = 16


@dataclass
class ScanConfig:
    """Configuration for file scanning operations.

    Attributes:
        chunk_size: Chunk size in bytes (power of two, >= 4096) used for partial/full hashing.
        hash_algorithm: Hash algorithm name (sha256/sha512/md5/sha1/xxhash64).
        parallel_workers: Number of worker processes (between 1 and 16).
        storage_type: Underlying storage type hint ("ssd" or "hdd").
    """

    chunk_size: int = 65536
    hash_algorithm: str = "xxhash64"
    parallel_workers: int = 4
    storage_type: Literal["ssd", "hdd"] = "ssd"

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        self._validate_chunk_size(self.chunk_size)
        self._validate_parallel_workers(self.parallel_workers)

    @staticmethod
    def _validate_chunk_size(value: int) -> None:
        """Validate chunk_size is a power of 2 and >= 4096."""
        if not ScanConfig._is_power_of_2(value):
            raise ValueError("chunk_size must be a power of 2")
        if value < MIN_CHUNK_SIZE:
            raise ValueError(f"chunk_size must be at least {MIN_CHUNK_SIZE}")

    @staticmethod
    def _validate_parallel_workers(value: int) -> None:
        """Validate parallel_workers is between 1 and 16."""
        if not (MIN_PARALLEL_WORKERS <= value <= MAX_PARALLEL_WORKERS):
            raise ValueError(
                f"parallel_workers must be between "
                f"{MIN_PARALLEL_WORKERS} and {MAX_PARALLEL_WORKERS}"
            )

    @staticmethod
    def _is_power_of_2(n: int) -> bool:
        """Check if a number is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0
