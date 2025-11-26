"""Scan configuration data model."""

from dataclasses import dataclass, field
from typing import Literal

# Constants for validation
MIN_CHUNK_SIZE = 4096
MIN_PARALLEL_WORKERS = 1
MAX_PARALLEL_WORKERS = 16


@dataclass
class ScanConfig:
    """Configuration for file scanning operations."""

    chunk_size: int = 65536
    hash_algorithm: str = "xxhash64"
    parallel_workers: int = 4
    storage_type: Literal["ssd", "hdd"] = "ssd"

    def __post_init__(self) -> None:
        """Validate configuration values after initialization."""
        self._validate_chunk_size(self.chunk_size)
        self._validate_parallel_workers(self.parallel_workers)

    def _validate_chunk_size(self, value: int) -> None:
        """Validate chunk_size is a power of 2 and >= 4096."""
        if not self._is_power_of_2(value):
            raise ValueError("chunk_size must be a power of 2")
        if value < MIN_CHUNK_SIZE:
            raise ValueError(f"chunk_size must be at least {MIN_CHUNK_SIZE}")

    def _validate_parallel_workers(self, value: int) -> None:
        """Validate parallel_workers is between 1 and 16."""
        if not (MIN_PARALLEL_WORKERS <= value <= MAX_PARALLEL_WORKERS):
            raise ValueError(
                f"parallel_workers must be between {MIN_PARALLEL_WORKERS} and {MAX_PARALLEL_WORKERS}"
            )

    @staticmethod
    def _is_power_of_2(n: int) -> bool:
        """Check if a number is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0
