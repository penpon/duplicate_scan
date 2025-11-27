"""
プログレスビュー - スキャン進捗を表示するUIコンポーネント
"""

from typing import Callable, Optional

import flet as ft


class ProgressView:
    """プログレスビューコントロール"""

    def __init__(self) -> None:
        """ProgressViewを初期化する"""
        self.page: Optional[ft.Page] = None
        self.cancel_callback: Optional[Callable[[], None]] = None

        # UIコンポーネント
        self.stage_label = ft.Text("Preparing...", size=16, weight=ft.FontWeight.BOLD)
        self.progress_bar = ft.ProgressBar(value=0.0)
        self.count_label = ft.Text("0/0", size=14)
        self.cancel_button = ft.ElevatedButton(
            "Cancel", on_click=self._on_cancel_clicked, icon=ft.Icons.CANCEL
        )

    def build(self) -> ft.Column:
        """
        UIを構築する

        Returns:
            ft.Column: メインUIコンテナ
        """
        return ft.Column(
            [
                ft.Text("Scanning Progress", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.stage_label,
                ft.Container(
                    content=self.progress_bar,
                    margin=ft.margin.symmetric(vertical=10),
                ),
                self.count_label,
                ft.Container(
                    content=self.cancel_button,
                    margin=ft.margin.only(top=20),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=10,
        )

    def update_progress(self, stage: str, current: int, total: int) -> None:
        """
        進捗を更新する

        Args:
            stage: 現在のステージ名
            current: 現在の進捗数
            total: 合計数
        """
        self.stage_label.value = stage

        if total > 0:
            self.progress_bar.value = current / total
            self.count_label.value = f"{current}/{total}"
        else:
            self.progress_bar.value = 0.0
            self.count_label.value = "0/0"

        if self.page:
            self.page.update()

    def set_indeterminate(self, stage: str) -> None:
        """
        不定モードに設定する

        Args:
            stage: 現在のステージ名
        """
        self.stage_label.value = stage
        self.progress_bar.value = None  # Fletのインデターミネート表示を使用
        self.count_label.value = "Processing..."

        if self.page:
            self.page.update()

    def set_cancel_callback(self, callback: Callable[[], None]) -> None:
        """
        キャンセルボタンのコールバックを設定する

        Args:
            callback: キャンセル時に呼ばれるコールバック関数
        """
        self.cancel_callback = callback

    def reset(self) -> None:
        """プログレス表示をリセットする"""
        self.stage_label.value = "Preparing..."
        self.progress_bar.value = 0.0
        self.count_label.value = "0/0"

        if self.page:
            self.page.update()

    def _on_cancel_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """キャンセルボタンがクリックされたときの処理"""
        if self.cancel_callback:
            self.cancel_callback()
