"""Test ScanningView UI component."""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

import flet as ft
from src.ui.scanning_view import ScanningView


class TestScanningView:
    """Test cases for ScanningView."""

    def test_scanning_view_initialization(self):
        """Test ScanningView can be initialized with default values."""
        # Given
        view = ScanningView()

        # When
        assert view.progress_bar.value == 0.0
        assert view.status_text.value == "準備中..."
        assert view.current_file_text.value == ""
        assert view.files_processed_text.value == "0 / 0"
        assert view.error_text.visible == False

    def test_scanning_view_update_progress(self):
        """Test progress updates work correctly."""
        # Given
        view = ScanningView()

        # When
        view.update_progress(0.5, "スキャン中...", "/test/file.jpg", 10, 20)

        # Then
        assert view.progress_bar.value == 0.5
        assert view.status_text.value == "スキャン中..."
        assert view.current_file_text.value == "/test/file.jpg"
        assert view.files_processed_text.value == "10 / 20"
        assert view.error_text.visible == False

    def test_scanning_view_update_progress_with_error(self):
        """Test progress updates with error display."""
        # Given
        view = ScanningView()

        # When
        view.update_progress(
            0.5, "スキャン中...", "/test/file.jpg", 10, 20, "アクセス権限エラー"
        )

        # Then
        assert view.progress_bar.value == 0.5
        assert view.status_text.value == "スキャン中..."
        assert view.current_file_text.value == "/test/file.jpg"
        assert view.files_processed_text.value == "10 / 20"
        assert view.error_text.visible == True
        assert view.error_text.value == "エラー: アクセス権限エラー"

    def test_scanning_view_reset(self):
        """Test view can be reset to initial state."""
        # Given
        view = ScanningView()
        view.update_progress(
            0.8, "完了", "/test/complete.jpg", 100, 100, "テストエラー"
        )

        # When
        view.reset()

        # Then
        assert view.progress_bar.value == 0.0
        assert view.status_text.value == "準備中..."
        assert view.current_file_text.value == ""
        assert view.files_processed_text.value == "0 / 0"
        assert view.error_text.visible == False
        assert view.error_text.value == ""

    def test_scanning_view_build_returns_control(self):
        """Test build method returns proper Flet control."""
        # Given
        view = ScanningView()

        # When
        control = view.build()

        # Then
        assert isinstance(control, ft.Column)
        assert (
            len(control.controls) == 6
        )  # title, progress_bar, status_text, current_file_text, files_processed_text, error_text

    def test_scanning_view_handles_invalid_progress_values(self):
        """Test view handles invalid progress values gracefully."""
        # Given
        view = ScanningView()

        # When/Then - should clamp values between 0 and 1
        view.update_progress(-0.5, "テスト", "", 0, 0)
        assert view.progress_bar.value == 0.0

        view.update_progress(1.5, "テスト", "", 0, 0)
        assert view.progress_bar.value == 1.0

    def test_scanning_view_progress_callback_integration(self):
        """Test view can be used as progress callback for scanner."""
        # Given
        view = ScanningView()
        mock_scanner = Mock()

        # Simulate scanner calling the callback
        progress_callback = view.get_progress_callback()

        # When
        progress_callback(
            current_file=Path("/test/current.jpg"),
            processed_count=5,
            total_count=10,
            status="ハッシュ計算中",
        )

        # Then
        assert view.progress_bar.value == 0.5
        assert view.status_text.value == "ハッシュ計算中"
        assert view.current_file_text.value == "/test/current.jpg"
        assert view.files_processed_text.value == "5 / 10"
        assert view.error_text.visible == False

    def test_scanning_view_progress_callback_with_error(self):
        """Test progress callback handles errors correctly."""
        # Given
        view = ScanningView()
        progress_callback = view.get_progress_callback()

        # When
        progress_callback(
            current_file=Path("/test/problem.jpg"),
            processed_count=3,
            total_count=10,
            status="エラー発生",
            error="ファイルが見つかりません",
        )

        # Then
        assert view.progress_bar.value == 0.3
        assert view.status_text.value == "エラー発生"
        assert view.current_file_text.value == "/test/problem.jpg"
        assert view.files_processed_text.value == "3 / 10"
        assert view.error_text.visible == True
        assert view.error_text.value == "エラー: ファイルが見つかりません"
