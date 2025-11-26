"""Tests for ScanConfig dataclass."""

import pytest
from typing import Literal

from src.models.scan_config import ScanConfig


class TestScanConfig:
    """Test cases for ScanConfig dataclass."""

    def test_default_values(self) -> None:
        """Test that ScanConfig has correct default values."""
        config = ScanConfig()

        assert config.chunk_size == 65536
        assert config.hash_algorithm == "xxhash64"
        assert config.parallel_workers == 4
        assert config.storage_type == "ssd"

    def test_custom_values(self) -> None:
        """Test ScanConfig with custom values."""
        config = ScanConfig(
            chunk_size=131072,
            hash_algorithm="sha256",
            parallel_workers=8,
            storage_type="hdd",
        )

        assert config.chunk_size == 131072
        assert config.hash_algorithm == "sha256"
        assert config.parallel_workers == 8
        assert config.storage_type == "hdd"

    def test_storage_type_literal(self) -> None:
        """Test that storage_type only accepts 'ssd' or 'hdd'."""
        # Valid values should work
        config_ssd = ScanConfig(storage_type="ssd")
        config_hdd = ScanConfig(storage_type="hdd")

        assert config_ssd.storage_type == "ssd"
        assert config_hdd.storage_type == "hdd"

    def test_chunk_size_validation_power_of_2(self) -> None:
        """Test that chunk_size must be a power of 2."""
        # Valid powers of 2 should work
        valid_sizes = [4096, 8192, 16384, 32768, 65536, 131072, 262144]
        for size in valid_sizes:
            config = ScanConfig(chunk_size=size)
            assert config.chunk_size == size

    def test_chunk_size_validation_minimum(self) -> None:
        """Test that chunk_size must be >= 4096."""
        # Valid minimum size should work
        config = ScanConfig(chunk_size=4096)
        assert config.chunk_size == 4096

    def test_chunk_size_validation_invalid(self) -> None:
        """Test that invalid chunk_size values raise ValueError."""
        # Non-power of 2 values should raise ValueError
        invalid_sizes = [1000, 4095, 4097, 5000, 65535, 65537]
        for size in invalid_sizes:
            with pytest.raises(ValueError, match="chunk_size must be a power of 2"):
                ScanConfig(chunk_size=size)

    def test_chunk_size_validation_too_small(self) -> None:
        """Test that chunk_size < 4096 raises ValueError."""
        with pytest.raises(ValueError, match="chunk_size must be at least 4096"):
            ScanConfig(chunk_size=2048)

    def test_parallel_workers_validation_range(self) -> None:
        """Test that parallel_workers must be between 1 and 16."""
        # Valid range should work
        valid_workers = [1, 2, 4, 8, 16]
        for workers in valid_workers:
            config = ScanConfig(parallel_workers=workers)
            assert config.parallel_workers == workers

    def test_parallel_workers_validation_invalid(self) -> None:
        """Test that invalid parallel_workers values raise ValueError."""
        # Values outside 1-16 range should raise ValueError
        invalid_workers = [0, -1, 17, 100]
        for workers in invalid_workers:
            with pytest.raises(
                ValueError, match="parallel_workers must be between 1 and 16"
            ):
                ScanConfig(parallel_workers=workers)

    def test_is_power_of_2_utility(self) -> None:
        """Test the internal _is_power_of_2 utility method."""
        # Test positive cases
        powers_of_2 = [1, 2, 4, 8, 16, 32, 64, 128, 4096, 65536]
        for n in powers_of_2:
            assert ScanConfig._is_power_of_2(n) is True

        # Test negative cases
        non_powers = [0, 3, 5, 6, 7, 9, 10, 4095, 65535]
        for n in non_powers:
            assert ScanConfig._is_power_of_2(n) is False
