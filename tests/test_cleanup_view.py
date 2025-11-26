"""Tests for the CleanupView UI component."""

from unittest.mock import MagicMock

import flet as ft

from src.services.deleter import DeleteResult
from src.ui.cleanup_view import CleanupView


class TestCleanupView:
    """Tests for CleanupView component."""

    def test_cleanup_view_initialization(self) -> None:
        """Test CleanupView can be initialized."""
        view = CleanupView()
        assert view is not None
        assert view.delete_result is None

    def test_cleanup_view_build(self) -> None:
        """Test CleanupView builds a valid Flet control."""
        view = CleanupView()
        control = view.build()

        assert isinstance(control, ft.Column)

    def test_cleanup_view_set_result(self) -> None:
        """Test setting delete result updates the view."""
        view = CleanupView()
        view.build()  # Build first to create UI components

        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg", "/path/to/file2.jpg"],
            failed_files=[],
            total_deleted=2,
            total_failed=0,
            space_saved=2048,
        )

        view.set_result(result)

        assert view.delete_result == result

    def test_cleanup_view_shows_deleted_count(self) -> None:
        """Test view displays correct deleted count."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg", "/path/to/file2.jpg"],
            failed_files=[],
            total_deleted=2,
            total_failed=0,
            space_saved=2048,
        )

        view.set_result(result)

        # Check that deleted count is displayed
        assert view.deleted_count_text.value == "2"

    def test_cleanup_view_shows_space_saved(self) -> None:
        """Test view displays correct space saved."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg"],
            failed_files=[],
            total_deleted=1,
            total_failed=0,
            space_saved=1024 * 1024 * 5,  # 5 MB
        )

        view.set_result(result)

        # Check that space saved is displayed
        assert view.space_saved_text.value == "5.0 MB"

    def test_cleanup_view_shows_failed_files(self) -> None:
        """Test view displays failed files."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=[],
            failed_files=[
                ("/path/to/fail1.jpg", "Permission denied"),
                ("/path/to/fail2.jpg", "File in use"),
            ],
            total_deleted=0,
            total_failed=2,
            space_saved=0,
        )

        view.set_result(result)

        # Check that failed count is displayed
        assert view.failed_count_text.value == "2"

    def test_cleanup_view_done_button(self) -> None:
        """Test done button exists and is clickable."""
        view = CleanupView()
        view.build()

        assert view.done_button is not None
        assert isinstance(view.done_button, ft.ElevatedButton)

    def test_cleanup_view_done_callback(self) -> None:
        """Test done button triggers callback."""
        view = CleanupView()
        view.build()

        callback = MagicMock()
        view.set_done_callback(callback)

        # Simulate button click
        view._on_done_clicked(None)

        callback.assert_called_once()

    def test_cleanup_view_empty_result(self) -> None:
        """Test view handles empty result."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=[],
            failed_files=[],
            total_deleted=0,
            total_failed=0,
            space_saved=0,
        )

        view.set_result(result)

        assert view.deleted_count_text.value == "0"
        assert view.space_saved_text.value == "0 B"

    def test_cleanup_view_large_space_saved(self) -> None:
        """Test view displays large space saved correctly."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=["/path/to/file.jpg"],
            total_deleted=1,
            total_failed=0,
            failed_files=[],
            space_saved=1024 * 1024 * 1024 * 2,  # 2 GB
        )

        view.set_result(result)

        assert view.space_saved_text.value == "2.0 GB"

    def test_cleanup_view_shows_deleted_files_list(self) -> None:
        """Test view shows list of deleted files."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg", "/path/to/file2.jpg"],
            failed_files=[],
            total_deleted=2,
            total_failed=0,
            space_saved=2048,
        )

        view.set_result(result)

        # Check that deleted files list is populated
        assert len(view.deleted_files_column.controls) == 2

    def test_cleanup_view_shows_failed_files_list(self) -> None:
        """Test view shows list of failed files with reasons."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=[],
            failed_files=[
                ("/path/to/fail1.jpg", "Permission denied"),
            ],
            total_deleted=0,
            total_failed=1,
            space_saved=0,
        )

        view.set_result(result)

        # Check that failed files list is populated
        assert len(view.failed_files_column.controls) == 1

    def test_cleanup_view_hides_failed_section_when_no_failures(self) -> None:
        """Test failed section is hidden when no failures."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=["/path/to/file1.jpg"],
            failed_files=[],
            total_deleted=1,
            total_failed=0,
            space_saved=1024,
        )

        view.set_result(result)

        # Failed section should be hidden
        assert view.failed_section.visible is False

    def test_cleanup_view_shows_failed_section_when_failures(self) -> None:
        """Test failed section is visible when there are failures."""
        view = CleanupView()
        view.build()

        result = DeleteResult(
            deleted_files=[],
            failed_files=[("/path/to/fail.jpg", "Error")],
            total_deleted=0,
            total_failed=1,
            space_saved=0,
        )

        view.set_result(result)

        # Failed section should be visible
        assert view.failed_section.visible is True

    def test_cleanup_view_back_to_home_button(self) -> None:
        """Test back to home button exists and is clickable."""
        view = CleanupView()
        view.build()

        assert view.back_to_home_button is not None
        assert isinstance(view.back_to_home_button, ft.ElevatedButton)
        assert view.back_to_home_button.text == "Scan Again"

    def test_cleanup_view_back_to_home_callback(self) -> None:
        """Test back to home button triggers callback."""
        view = CleanupView()
        view.build()

        callback = MagicMock()
        view.set_back_to_home_callback(callback)

        # Simulate button click
        view._on_back_to_home_clicked(None)

        callback.assert_called_once()
