"""
ホームビュー - フォルダ選択画面
"""

from typing import List, Optional
from pathlib import Path
import logging

import flet as ft


class HomeView:
    """ホームビューコントロール"""

    def __init__(self) -> None:
        """HomeViewを初期化する"""
        self.selected_folders: List[str] = []
        self.page: Optional[ft.Page] = None

        # UIコンポーネント
        self.folder_list = ft.ListView(expand=True, height=200)
        self.start_button = ft.ElevatedButton(
            "Start Scan", on_click=self._on_start_scan_clicked, disabled=True
        )
        self.add_folder_button = ft.ElevatedButton(
            "Add Folder", on_click=self._on_add_folder_clicked
        )
        self.clear_button = ft.ElevatedButton(
            "Clear All", on_click=self._on_clear_clicked
        )

        # File picker
        self.file_picker = ft.FilePicker(on_result=self._on_folder_picked)

    def build(self) -> ft.Column:
        """
        UIを構築する

        Returns:
            ft.Column: メインUIコンテナ
        """
        return ft.Column(
            [
                ft.Text(
                    "Duplicate File Scanner",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "Select folders to scan for duplicate files",
                    size=16,
                ),
                ft.Divider(),
                ft.Row(
                    [
                        self.add_folder_button,
                        self.clear_button,
                    ],
                    alignment=ft.MainAxisAlignment.START,
                ),
                ft.Text("Selected Folders:", weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=self.folder_list,
                    border=ft.border.all(1, ft.Colors.OUTLINE),
                    border_radius=8,
                    padding=10,
                    margin=ft.margin.only(bottom=20),
                ),
                ft.Row(
                    [
                        self.start_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                # file_picker is in page.overlay, not here
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

    def add_folder(self, folder_path: str) -> None:
        """
        フォルダをリストに追加する

        Args:
            folder_path: 追加するフォルダのパス
        """
        if not self._is_valid_folder(folder_path):
            return

        if folder_path not in self.selected_folders:
            self.selected_folders.append(folder_path)
            if self.page:
                self._update_folder_list()
                self._update_start_button()

    def remove_folder(self, folder_path: str) -> None:
        """
        フォルダをリストから削除する

        Args:
            folder_path: 削除するフォルダのパス
        """
        if folder_path in self.selected_folders:
            self.selected_folders.remove(folder_path)
            if self.page:
                self._update_folder_list()
                self._update_start_button()

    def clear_folders(self) -> None:
        """すべてのフォルダをクリアする"""
        self.selected_folders.clear()
        if self.page:
            self._update_folder_list()
            self._update_start_button()

    def can_start_scan(self) -> bool:
        """
        スキャンを開始できるかどうかを返す

        Returns:
            bool: スキャン開始可能ならTrue
        """
        return len(self.selected_folders) > 0

    def _is_valid_folder(self, folder_path: str) -> bool:
        """
        フォルダパスが有効かどうかをチェックする

        Args:
            folder_path: チェックするフォルダパス

        Returns:
            bool: 有効なフォルダならTrue
        """
        try:
            # 基本的なパス形式チェック
            if not folder_path or folder_path.strip() == "":
                return False

            # 実際の環境では存在チェックも行う
            path = Path(folder_path)
            return path.exists() and path.is_dir()
        except (OSError, PermissionError, Exception):
            return False

    def _update_folder_list(self) -> None:
        """フォルダリストのUIを更新する"""
        if not self.page:
            return

        self.folder_list.controls.clear()

        for folder in self.selected_folders:
            folder_item = ft.ListTile(
                leading=ft.Icon(ft.Icons.FOLDER),
                title=ft.Text(folder),
                trailing=ft.IconButton(
                    ft.Icons.DELETE,
                    on_click=lambda _, f=folder: self.remove_folder(f),
                ),
            )
            self.folder_list.controls.append(folder_item)

        self.page.update()

    def _update_start_button(self) -> None:
        """Start Scanボタンの状態を更新する"""
        self.start_button.disabled = not self.can_start_scan()
        if self.page:
            self.page.update()

    def _on_add_folder_clicked(self, e: ft.ControlEvent) -> None:
        """Add Folderボタンがクリックされたときの処理"""
        if self.page:
            logging.info("Add Folder button clicked - opening directory picker")
            try:
                # macOSでのFilePicker問題対応：代替手段を試行
                self.file_picker.get_directory_path(
                    dialog_title="Select folder to scan"
                )
                logging.info("Directory picker dialog opened")

                # ユーザーへのフィードバック
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Opening folder selection dialog..."),
                    bgcolor=ft.Colors.BLUE_600,
                )
                self.page.snack_bar.open = True
                self.page.update()

            except Exception as ex:
                logging.error(f"Failed to open directory picker: {ex}")
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Error: {ex}"),
                        bgcolor=ft.Colors.RED_600,
                    )
                    self.page.snack_bar.open = True
                    self.page.update()

    def _on_folder_picked(self, e: ft.FilePickerResultEvent) -> None:
        """フォルダが選択されたときの処理"""
        logging.info(f"Folder picker result: path={e.path}")
        if e.path:
            self.add_folder(e.path)
        else:
            logging.info("Folder selection cancelled")

    def _on_clear_clicked(self, e: ft.ControlEvent) -> None:
        """Clear Allボタンがクリックされたときの処理"""
        logging.info("Clear All button clicked")
        self.clear_folders()
        if self.page:
            # フィードバックを表示
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("All folders cleared"),
                bgcolor=ft.Colors.GREEN_600,
            )
            self.page.snack_bar.open = True
            self.page.update()

    def _on_start_scan_clicked(self, e: ft.ControlEvent) -> None:
        """Start Scanボタンがクリックされたときの処理"""
        # このメソッドは親コントローラーによってオーバーライドされる
        pass
