"""Duplicate file scanner application built with Flet."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List

import flet as ft

from src.models.file_meta import FileMeta
from src.services.deleter import Deleter
from src.services.detector import DuplicateDetector
from src.services.hasher import Hasher
from src.ui.cleanup_view import CleanupView
from src.ui.home_view import HomeView
from src.ui.results_view import ResultsView

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
        self.hasher = Hasher()
        self.detector = DuplicateDetector()

        # Create explicit backup directory
        self.backup_dir = Path.home() / ".duplicate_scan_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.deleter = Deleter(self.backup_dir)
        self.results_view = ResultsView()
        self.cleanup_view = CleanupView()
        self.home_content: ft.Column | None = None
        # FilePicker はページの overlay に追加しないとダイアログが開かない
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)

    def _collect_files(self, folders: List[str]) -> List[FileMeta]:
        """フォルダからファイルを収集する

        Args:
            folders: スキャンするフォルダのリスト

        Returns:
            収集されたファイルのメタデータリスト
        """
        files: List[FileMeta] = []
        for folder in folders:
            folder_path = Path(folder)
            if not folder_path.exists() or not folder_path.is_dir():
                continue

            for root, _, filenames in os.walk(folder):
                for filename in filenames:
                    try:
                        file_path = Path(root) / filename
                        is_regular = file_path.is_file()
                        is_visible = not file_path.name.startswith(".")
                        if is_regular and is_visible:
                            stat = file_path.stat()
                            file_meta = FileMeta(
                                path=str(file_path),
                                size=stat.st_size,
                                modified_time=datetime.fromtimestamp(stat.st_mtime),
                            )
                            files.append(file_meta)
                    except (OSError, PermissionError) as ex:
                        logging.warning(f"Cannot access file {filename}: {ex}")
        return files

    def _compute_hashes(self, files: List[FileMeta]) -> List[FileMeta]:
        """ファイルのハッシュを計算する

        Args:
            files: ハッシュを計算するファイルリスト

        Returns:
            ハッシュ計算済みのファイルリスト
        """
        for file in files:
            try:
                file.partial_hash = self.hasher.calculate_partial_hash(file.path)
                file.full_hash = self.hasher.calculate_full_hash(file.path)
            except (OSError, FileNotFoundError) as ex:
                logging.warning(f"Cannot hash file {file.path}: {ex}")
        return files

    def _on_start_scan_clicked(self, e: ft.ControlEvent) -> None:
        """スキャン開始ボタンがクリックされたときの処理"""
        selected_folders = self.selected_folders
        if not selected_folders or not self.page:
            return

        logging.info(f"Scanning folders: {selected_folders}")

        # 進捗表示
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Scanning {len(selected_folders)} folder(s)..."),
            bgcolor=ft.Colors.BLUE_600,
        )
        self.page.snack_bar.open = True
        self.page.update()

        # ファイル収集
        logging.info("Collecting files...")
        files = self._collect_files(selected_folders)
        logging.info(f"Found {len(files)} files")

        if not files:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("No files found in selected folders."),
                bgcolor=ft.Colors.ORANGE_600,
            )
            self.page.snack_bar.open = True
            self.page.update()
            return

        # ハッシュ計算
        logging.info("Computing hashes...")
        files_with_hashes = self._compute_hashes(files)

        # 重複検出
        logging.info("Detecting duplicates...")
        duplicate_groups = self.detector.find_duplicates(files_with_hashes)
        logging.info(f"Found {len(duplicate_groups)} duplicate groups")

        # 結果表示
        self._show_results(duplicate_groups)

    def _show_results(self, duplicate_groups: list) -> None:
        """結果画面を表示する

        Args:
            duplicate_groups: 重複グループのリスト
        """
        if not self.page:
            return

        # ResultsViewにページを設定
        self.results_view.page = self.page

        # 削除コールバックを設定
        self.results_view.set_delete_callback(self._on_delete_files)

        # 重複グループを設定
        self.results_view.set_duplicate_groups(duplicate_groups)

        # 結果メッセージ
        total_duplicates = sum(len(g.files) for g in duplicate_groups)
        if duplicate_groups:
            msg = (
                f"Found {len(duplicate_groups)} groups "
                f"with {total_duplicates} duplicate files"
            )
            color = ft.Colors.GREEN_600
        else:
            msg = "No duplicate files found"
            color = ft.Colors.ORANGE_600

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(msg),
            bgcolor=color,
        )
        self.page.snack_bar.open = True

        # ページをクリアして結果ビューを表示
        self.page.controls.clear()
        self.page.add(self.results_view.build())
        self.page.update()

        logging.info(msg)

    def _on_delete_files(self, files: List[FileMeta]) -> None:
        """選択されたファイルを削除する

        Args:
            files: 削除するファイルのリスト
        """
        if not self.page or not files:
            return

        logging.info(f"Deleting {len(files)} files...")

        # 進捗表示
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Moving {len(files)} file(s) to backup..."),
            bgcolor=ft.Colors.BLUE_600,
        )
        self.page.snack_bar.open = True
        self.page.update()

        # ファイルを削除（バックアップディレクトリに移動）
        result = self.deleter.delete_files(files)

        logging.info(
            f"Deleted {result.total_deleted} files, failed {result.total_failed} files"
        )
        if result.backup_directory:
            logging.info(f"Backup directory: {result.backup_directory}")

            # Show backup directory to user
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(
                    f"Files backed up to: {result.backup_directory}",
                    bgcolor=ft.Colors.BLUE_600,
                ),
                duration=10000,  # Show for 10 seconds
            )
            self.page.snack_bar.open = True
            self.page.update()

        # CleanupViewを表示
        self._show_cleanup(result)

    def _show_cleanup(self, result) -> None:
        """クリーンアップ結果画面を表示する

        Args:
            result: 削除結果
        """
        if not self.page:
            return

        # CleanupViewにページを設定
        self.cleanup_view.page = self.page

        # 完了コールバックを設定
        self.cleanup_view.set_done_callback(self._on_cleanup_done)

        # 結果を設定
        self.cleanup_view.set_result(result)

        # ページをクリアしてクリーンアップビューを表示
        self.page.controls.clear()
        self.page.add(self.cleanup_view.build())
        self.page.update()

    def _on_cleanup_done(self) -> None:
        """クリーンアップ完了後にホーム画面に戻る"""
        if not self.page:
            return

        # ホーム画面に戻る
        self.page.controls.clear()
        self.page.add(self.build())
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
