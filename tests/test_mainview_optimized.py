"""Tests for MainView integration with optimized scanning."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from src.main import MainView
from src.models.scan_config import ScanConfig
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher
from src.models.file_meta import FileMeta


class TestMainViewOptimizedIntegration:
    """Test MainView integration with optimized scanning pipeline."""

    def test_mainview_uses_optimized_scanning(self):
        """Test that MainView uses find_duplicates_optimized instead of old method."""
        # Given
        mock_page = Mock()
        main_view = MainView(mock_page)

        # Create temporary test files
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file1 = Path(temp_dir) / "test1.txt"
            test_file2 = Path(temp_dir) / "test2.txt"

            test_file1.write_text("test content")
            test_file2.write_text("test content")

            main_view.selected_folders = [str(temp_dir)]

            # When & Then
            # This test will fail initially because MainView doesn't use optimized scanning
            with patch("src.main.DuplicateDetector") as mock_detector_class:
                mock_detector = Mock()
                mock_detector_class.return_value = mock_detector

                # Mock the optimized method to exist and be called
                mock_detector.find_duplicates_optimized = Mock(return_value=[])

                # Trigger scan
                main_view._on_start_scan_clicked(Mock())

                # Should call optimized method, not old one
                mock_detector.find_duplicates_optimized.assert_called_once()

    def test_scanconfig_created_with_optimal_defaults(self):
        """Test that ScanConfig is created with optimal default values."""
        # Given
        mock_page = Mock()
        main_view = MainView(mock_page)

        with tempfile.TemporaryDirectory() as temp_dir:
            main_view.selected_folders = [temp_dir]

            # Create mock file to avoid early return
            mock_file = Mock()

            # When & Then
            with (
                patch("src.main.ScanConfig") as mock_config_class,
                patch("src.main.Hasher") as mock_hasher_class,
                patch("src.main.DuplicateDetector") as mock_detector_class,
                patch.object(main_view, "_collect_files", return_value=[mock_file]),
            ):
                mock_config = Mock()
                mock_config_class.return_value = mock_config
                mock_detector = Mock()
                mock_detector_class.return_value = mock_detector
                mock_detector.find_duplicates_optimized = Mock(return_value=[])

                # Trigger scan
                main_view._on_start_scan_clicked(Mock())

                # The config should be created with optimal defaults
                mock_config_class.assert_called_once_with(
                    chunk_size=65536,
                    hash_algorithm="xxhash64",
                    parallel_workers=4,
                    storage_type="ssd",
                )

    def test_progress_callback_passed_to_detector(self):
        """Test that progress callback is properly passed to detector."""
        # Given
        mock_page = Mock()
        main_view = MainView(mock_page)

        with tempfile.TemporaryDirectory() as temp_dir:
            main_view.selected_folders = [temp_dir]

            # Create mock file to avoid early return
            mock_file = Mock()

            # When & Then
            with (
                patch("src.main.ScanConfig"),
                patch("src.main.Hasher") as mock_hasher_class,
                patch("src.main.DuplicateDetector") as mock_detector_class,
                patch.object(main_view, "_collect_files", return_value=[mock_file]),
            ):
                mock_detector = Mock()
                mock_detector_class.return_value = mock_detector
                mock_detector.find_duplicates_optimized = Mock(return_value=[])

                # Trigger scan
                main_view._on_start_scan_clicked(Mock())

                # Should call with progress callback
                call_args = mock_detector.find_duplicates_optimized.call_args
                assert call_args is not None
                assert len(call_args[0]) >= 3  # files, hasher, progress_callback
                assert callable(call_args[0][2])  # progress_callback should be callable

    def test_old_compute_hashes_method_removed(self):
        """Test that _compute_hashes method is removed from MainView."""
        # Given
        mock_page = Mock()
        main_view = MainView(mock_page)

        # When & Then
        # This test will fail if _compute_hashes method still exists
        assert not hasattr(main_view, "_compute_hashes"), (
            "_compute_hashes method should be removed from MainView"
        )

    def test_error_handling_maintained(self):
        """Test that error handling is maintained after optimization."""
        # Given
        mock_page = Mock()
        main_view = MainView(mock_page)
        main_view.selected_folders = ["/nonexistent/path"]

        # When & Then
        # Should handle errors gracefully
        try:
            main_view._on_start_scan_clicked(Mock())
            # If no exception, should show error message
            assert mock_page.snack_bar is not None
        except Exception:
            # If exception occurs, it should be handled properly
            pytest.fail("Error handling should prevent exceptions from bubbling up")
