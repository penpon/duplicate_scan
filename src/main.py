"""Duplicate file scanner application built with Flet."""

import flet as ft
from src.ui.home_view import HomeView


class MainView(HomeView):
    """メインビュー - HomeViewを拡張してスキャン開始処理を実装"""

    def __init__(self, page: ft.Page) -> None:
        super().__init__()
        self.page = page

    def _on_start_scan_clicked(self, e: ft.ControlEvent) -> None:
        """スキャン開始ボタンがクリックされたときの処理"""
        selected_folders = self.selected_folders
        if selected_folders and self.page:
            # TODO: スキャン画面に遷移する処理を実装
            print(f"Scanning folders: {selected_folders}")
            # 仮の通知
            snack_bar = ft.SnackBar(
                content=ft.Text(f"Starting scan of {len(selected_folders)} folders..."),
                bgcolor=ft.colors.BLUE_600,
            )
            self.page.overlay.append(snack_bar)
            snack_bar.open = True
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
