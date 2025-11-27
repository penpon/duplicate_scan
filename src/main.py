"""Duplicate file scanner application built with Flet."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import flet as ft

from src.ui.home_view import HomeView
from src.ui.results_view import ResultsView
from src.models.file_meta import FileMeta
from src.models.scan_config import ScanConfig
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class MainView(HomeView):
    """メインビュー - HomeViewを拡張してスキャン開始処理を実装"""

    def __init__(self, page: ft.Page) -> None:
        super().__init__()
        self.page = page
        self.results_view: Optional[ResultsView] = None

    def _on_start_scan_clicked(self, e: ft.ControlEvent) -> None:
        """スキャン開始ボタンがクリックされたときの処理"""
        selected_folders = self.selected_folders
        if not selected_folders or not self.page:
            return

        try:
            # Show progress notification
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Starting scan of {len(selected_folders)} folders..."),
                bgcolor=ft.Colors.BLUE_600,
            )
            self.page.snack_bar.open = True
            self.page.update()

            # Collect files from selected folders
            files = self._collect_files(selected_folders)
            if not files:
                self._show_error("No files found in selected folders")
                return

            # Create optimized configuration
            config = ScanConfig(
                chunk_size=65536,
                hash_algorithm="xxhash64",
                parallel_workers=4,
                storage_type="ssd",
            )

            # Initialize services with optimized config
            hasher = Hasher(config)
            detector = DuplicateDetector()

            # Define progress callback
            def progress_callback(message: str, current: int, total: int) -> None:
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"{message}: {current}/{total}"),
                        bgcolor=ft.Colors.GREEN_600,
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

            # Run optimized duplicate detection
            duplicate_groups = detector.find_duplicates_optimized(
                files, hasher, progress_callback
            )

            # Show results
            self._show_results(duplicate_groups)

        except Exception as ex:
            logging.error(f"Scan failed: {ex}")
            self._show_error(f"Scan failed: {str(ex)}")

    def _collect_files(self, folders: List[str]) -> List[FileMeta]:
        """指定されたフォルダからファイルを収集する"""
        files: List[FileMeta] = []

        for folder_path in folders:
            try:
                folder = Path(folder_path)
                if not folder.exists() or not folder.is_dir():
                    continue

                # Collect all files recursively
                for file_path in folder.rglob("*"):
                    if file_path.is_file():
                        try:
                            stat = file_path.stat()
                            file_meta = FileMeta(
                                path=str(file_path),
                                size=stat.st_size,
                                modified_time=datetime.fromtimestamp(stat.st_mtime),
                            )
                            files.append(file_meta)
                        except (OSError, PermissionError):
                            # Skip files that can't be accessed
                            continue

            except (OSError, PermissionError):
                continue

        return files

    def _show_results(self, duplicate_groups) -> None:
        """重複ファイルの結果を表示する"""
        if not self.page:
            return

        # Create or update results view
        self.results_view = ResultsView()
        self.results_view.set_duplicate_groups(duplicate_groups)

        # Clear current content and show results
        self.page.controls.clear()
        self.page.add(self.results_view.build())
        self.page.update()

    def _show_error(self, message: str) -> None:
        """エラーメッセージを表示する"""
        if not self.page:
            return

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.RED_600,
        )
        self.page.snack_bar.open = True
        self.page.update()


def main(page: ft.Page) -> None:
    """Main entry point for the Flet application.

    Args:
        page: The Flet page instance
    """
    page.title = "Duplicate File Scanner"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20
    page.scrollbar = True

    # MainViewの作成とページに追加
    main_view = MainView(page)
    page.add(main_view.build())


if __name__ == "__main__":
    ft.app(target=main)
