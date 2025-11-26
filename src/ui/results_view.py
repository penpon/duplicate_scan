"""
結果ビュー - 重複ファイルのリストと選択インターフェース
"""

from typing import Callable, Dict, List, Optional, Set

import flet as ft

from ..models.file_meta import FileMeta
from ..models.duplicate_group import DuplicateGroup


class ResultsView:
    """結果ビューコントロール"""

    def __init__(self) -> None:
        """ResultsViewを初期化する"""
        self.duplicate_groups: List[DuplicateGroup] = []
        self.selected_files: Set[FileMeta] = set()
        self.file_checkboxes: Dict[FileMeta, ft.Checkbox] = {}
        self.page: Optional[ft.Page] = None
        self.delete_callback: Optional[Callable[[List[FileMeta]], None]] = None

        # UIコンポーネント
        self.groups_column = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        self.delete_button = ft.ElevatedButton(
            "Delete Selected",
            on_click=self._on_delete_clicked,
            disabled=True,
            icon=ft.Icons.DELETE,
        )
        self.select_all_duplicates_button = ft.ElevatedButton(
            "Select All Duplicates",
            on_click=self._on_select_all_duplicates_clicked,
            icon=ft.Icons.SELECT_ALL,
            tooltip="Keep oldest file, select others for deletion",
        )

    def build(self) -> ft.Column:
        """
        UIを構築する

        Returns:
            ft.Column: メインUIコンテナ
        """
        return ft.Column(
            [
                ft.Text("Scan Results", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Select files to delete", size=16),
                ft.Divider(),
                ft.Row(
                    [
                        self.select_all_duplicates_button,
                        ft.ElevatedButton(
                            "Clear Selection",
                            on_click=self._on_clear_selection_clicked,
                            icon=ft.Icons.CLEAR,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    spacing=10,
                ),
                self.groups_column,
                ft.Divider(),
                ft.Row(
                    [
                        self.delete_button,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            expand=True,
        )

    def set_duplicate_groups(self, groups: List[DuplicateGroup]) -> None:
        """
        重複グループを設定する

        Args:
            groups: 重複グループのリスト
        """
        self.duplicate_groups = groups
        self._update_groups_list()
        if self.page:
            self.page.update()

    def toggle_file_selection(self, file: FileMeta) -> None:
        """
        ファイルの選択状態を切り替える

        Args:
            file: 選択状態を切り替えるファイル
        """
        # 選択状態を切り替え
        if file in self.selected_files:
            self.selected_files.remove(file)
        else:
            self.selected_files.add(file)

        # UI更新（バッチ処理で複数回のupdateを避ける）
        self._update_delete_button()
        self._update_file_checkbox(file)

        if self.page:
            self.page.update()

    def get_selected_files(self) -> List[FileMeta]:
        """
        選択されたファイルのリストを取得する

        Returns:
            List[FileMeta]: 選択されたファイルのリスト
        """
        return list(self.selected_files)

    def clear_selection(self) -> None:
        """選択をクリアする"""
        if not self.selected_files:
            return  # すでに空の場合は早期リターン

        self.selected_files.clear()
        self._update_delete_button()

        # チェックボックスの状態を更新
        self._update_all_checkboxes()

        if self.page:
            self.page.update()

    def set_delete_callback(self, callback: Callable[[List[FileMeta]], None]) -> None:
        """
        削除ボタンのコールバックを設定する

        Args:
            callback: 削除時に呼ばれるコールバック関数
        """
        self.delete_callback = callback

    def _update_groups_list(self) -> None:
        """重複グループリストのUIを更新する"""
        self.groups_column.controls.clear()
        self.file_checkboxes.clear()
        self.selected_files.clear()
        self._update_delete_button()

        if not self.duplicate_groups:
            self.groups_column.controls.append(
                ft.Text("No duplicate files found", size=16, italic=True)
            )
            return

        for group in self.duplicate_groups:
            group_item = self._create_group_item(group)
            self.groups_column.controls.append(group_item)

    def _create_group_item(self, group: DuplicateGroup) -> ft.Card:
        """
        重複グループのUIアイテムを作成する

        Args:
            group: 重複グループ

        Returns:
            ft.Card: グループのUIカード
        """
        files_list = ft.Column(spacing=5)

        for file in group.files:
            file_item = self._create_file_item(file)
            files_list.controls.append(file_item)

        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.ListTile(
                            leading=ft.Icon(ft.Icons.FOLDER_OPEN),
                            title=ft.Text(f"{len(group.files)} files"),
                            subtitle=ft.Text(
                                f"Total size: "
                                f"{self._format_file_size(group.total_size)}"
                            ),
                        ),
                        ft.Container(
                            content=files_list,
                            padding=ft.padding.only(left=16),
                        ),
                    ]
                ),
                padding=10,
            ),
            margin=ft.margin.only(bottom=10),
        )

    def _create_file_item(self, file: FileMeta) -> ft.ListTile:
        """
        ファイルアイテムのUIを作成する

        Args:
            file: ファイルメタデータ

        Returns:
            ft.ListTile: ファイルのUIアイテム
        """
        checkbox = ft.Checkbox(
            value=file in self.selected_files,
            on_change=lambda _, f=file: self.toggle_file_selection(f),
        )
        self.file_checkboxes[file] = checkbox

        return ft.ListTile(
            leading=checkbox,
            title=ft.Text(file.path, size=14),
            subtitle=ft.Text(
                f"{self._format_file_size(file.size)} • "
                f"{file.modified_time.strftime('%Y-%m-%d %H:%M')}",
                size=12,
            ),
            trailing=ft.Icon(
                ft.Icons.IMAGE
                if file.path.lower().endswith((".jpg", ".png", ".gif"))
                else ft.Icons.INSERT_DRIVE_FILE
            ),
        )

    def _update_delete_button(self) -> None:
        """削除ボタンの状態を更新する"""
        is_disabled = len(self.selected_files) == 0
        if self.delete_button.disabled != is_disabled:
            self.delete_button.disabled = is_disabled

    def _update_file_checkbox(self, file: FileMeta) -> None:
        """特定ファイルのチェックボックス状態を更新する"""
        checkbox = self.file_checkboxes.get(file)
        if not checkbox:
            return

        is_selected = file in self.selected_files
        if checkbox.value != is_selected:
            checkbox.value = is_selected
            if getattr(checkbox, "page", None):
                checkbox.update()

    def _update_all_checkboxes(self) -> None:
        """すべてのチェックボックス状態を更新する"""
        for file, checkbox in self.file_checkboxes.items():
            is_selected = file in self.selected_files
            if checkbox.value != is_selected:
                checkbox.value = is_selected
                if getattr(checkbox, "page", None):
                    checkbox.update()

    def _format_file_size(self, size_bytes: int) -> str:
        """
        ファイルサイズを人間が読める形式にフォーマットする

        Args:
            size_bytes: バイト単位のサイズ

        Returns:
            str: フォーマットされたサイズ文字列
        """
        if size_bytes >= 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        elif size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        elif size_bytes >= 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes} B"

    def _on_delete_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """削除ボタンがクリックされたときの処理"""
        selected_files = self.get_selected_files()
        if selected_files and self.delete_callback:
            self.delete_callback(selected_files)

    def _on_clear_selection_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """選択クリアボタンがクリックされたときの処理"""
        self.clear_selection()

    def _on_select_all_duplicates_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """全重複ファイル選択ボタンがクリックされたときの処理

        各グループで最も古いファイル（オリジナル）を残し、
        他のファイルを削除対象として選択する
        """
        self.select_all_duplicates()

    def select_all_duplicates(self) -> None:
        """各グループで最も古いファイルを残し、他を選択する"""
        self.selected_files.clear()

        for group in self.duplicate_groups:
            if len(group.files) < 2:
                continue

            # 最も古いファイル（オリジナル）を特定
            sorted_files = sorted(group.files, key=lambda f: f.modified_time)
            original = sorted_files[0]

            # オリジナル以外を選択
            for file in group.files:
                if file != original:
                    self.selected_files.add(file)

        # UI更新
        self._update_delete_button()
        self._update_all_checkboxes()

        if self.page:
            self.page.update()
