"""Tests for main module."""

from src.main import main


def test_main_function():
    """Test main function exists and is callable."""
    # Given: main function is imported
    # When: Checking if main is callable
    # Then: main should be a callable function
    assert callable(main)
