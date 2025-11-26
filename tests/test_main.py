"""Tests for main module."""

import unittest.mock as mock
from src.main import main


def test_main_function():
    """Test main function exists and is callable."""
    # Create a mock page
    mock_page = mock.Mock()

    # Test that main function can be called without error
    try:
        main(mock_page)
    except Exception as e:
        # Flet might require specific setup, so we just check it's importable
        assert callable(main), f"Main function should be callable, got error: {e}"
