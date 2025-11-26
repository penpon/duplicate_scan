"""Scanning View UI component for displaying scan progress."""

from typing import Callable, Optional
from pathlib import Path

import flet as ft


class ScanningView:
    """UI component for displaying progress during file scanning operations."""

    def __init__(self) -> None:
        """Initialize ScanningView with default UI elements."""
        self.progress_bar = ft.ProgressBar(
            visible=True,
            value=0.0,
            bar_height=6,
            color=ft.Colors.BLUE_400,
            bgcolor=ft.Colors.GREY_200,
        )
        self.status_text = ft.Text("準備中...", size=16, weight=ft.FontWeight.NORMAL)
        self.current_file_text = ft.Text("", size=12, color=ft.Colors.GREY_600)
        self.files_processed_text = ft.Text(
            "0 / 0", size=12, weight=ft.FontWeight.NORMAL
        )
        self.error_text = ft.Text("", size=12, color=ft.Colors.RED_400, visible=False)

    def update_progress(
        self,
        progress: float,
        status: str,
        current_file: str,
        processed_count: int,
        total_count: int,
        error: Optional[str] = None,
    ) -> None:
        """Update the progress display.

        Args:
            progress: Progress value between 0.0 and 1.0
            status: Current status message
            current_file: Path to the file currently being processed
            processed_count: Number of files processed so far
            total_count: Total number of files to process
            error: Optional error message to display
        """
        # Clamp progress between 0 and 1
        self.progress_bar.value = max(0.0, min(1.0, progress))
        self.status_text.value = status
        self.current_file_text.value = current_file
        self.files_processed_text.value = f"{processed_count} / {total_count}"

        # Handle error display
        if error:
            self.error_text.value = f"エラー: {error}"
            self.error_text.visible = True
        else:
            self.error_text.visible = False

    def reset(self) -> None:
        """Reset the view to its initial state."""
        self.progress_bar.value = 0.0
        self.status_text.value = "準備中..."
        self.current_file_text.value = ""
        self.files_processed_text.value = "0 / 0"
        self.error_text.visible = False
        self.error_text.value = ""

    def build(self) -> ft.Column:
        """Build and return the Flet control tree.

        Returns:
            A Column containing all the UI elements
        """
        return ft.Column(
            [
                ft.Text("スキャン中...", size=20, weight=ft.FontWeight.BOLD),
                self.progress_bar,
                self.status_text,
                self.current_file_text,
                self.files_processed_text,
                self.error_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            expand=True,
        )

    def get_progress_callback(
        self,
    ) -> Callable[[Path, int, int, str, Optional[str]], None]:
        """Get a callback function that can be used by scanning services.

        Returns:
            A callback function that updates the UI when called
        """

        def callback(
            current_file: Path,
            processed_count: int,
            total_count: int,
            status: str,
            error: Optional[str] = None,
        ) -> None:
            progress = processed_count / total_count if total_count > 0 else 0.0
            self.update_progress(
                progress=progress,
                status=status,
                current_file=str(current_file),
                processed_count=processed_count,
                total_count=total_count,
                error=error,
            )

        return callback
