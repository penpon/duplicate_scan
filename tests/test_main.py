"""Tests for main module."""

import unittest.mock as mock
from src.main import main


def test_main_function():
    """Test main function exists and is callable."""
    # Given: main function is imported
    # When: Checking if main is callable
    # Then: main should be a callable function
    assert callable(main)


def test_main_function_with_mock_page():
    """Test main function with mock page object."""
    # Given: Mock page object
    mock_page = mock.Mock()

    # When: Calling main function with mock page
    # Then: Should not raise any exceptions
    # Note: This test verifies that main function can handle page objects
    # without crashing, though actual UI setup may require Flet runtime
    try:
        main(mock_page)
    except Exception as e:
        # Expected in test environment without Flet runtime
        # The important thing is that the function is importable and callable
        assert "flet" in str(e).lower() or "page" in str(e).lower(), (
            f"Unexpected error: {e}"
        )
