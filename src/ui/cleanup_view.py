"""CleanupView - Display deletion results and summary."""

from typing import Callable, Optional

import flet as ft

from ..services.deleter import DeleteResult, Deleter


class CleanupView:
    """View for displaying cleanup/deletion results."""

    def __init__(self) -> None:
        """Initialize CleanupView."""
        self.delete_result: Optional[DeleteResult] = None
        self.page: Optional[ft.Page] = None
        self.done_callback: Optional[Callable[[], None]] = None

        # UI components - will be created in build()
        self.deleted_count_text: ft.Text = ft.Text("0", size=48, weight="bold")
        self.space_saved_text: ft.Text = ft.Text("0 B", size=24)
        self.failed_count_text: ft.Text = ft.Text("0", size=24)
        self.deleted_files_column: ft.Column = ft.Column(
            spacing=5, scroll=ft.ScrollMode.AUTO
        )
        self.failed_files_column: ft.Column = ft.Column(
            spacing=5, scroll=ft.ScrollMode.AUTO
        )
        self.failed_section: ft.Container = ft.Container(visible=False)
        self.done_button: ft.ElevatedButton = ft.ElevatedButton(
            "Done",
            on_click=self._on_done_clicked,
            icon=ft.Icons.CHECK,
        )
        self.back_to_home_button: ft.ElevatedButton = ft.ElevatedButton(
            "Scan Again",
            on_click=self._on_back_to_home_clicked,
            icon=ft.Icons.REFRESH,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        )
        self.back_to_home_callback: Optional[Callable[[], None]] = None

    def build(self) -> ft.Column:
        """
        Build the UI.

        Returns:
            ft.Column: Main UI container.
        """
        # Success section
        success_section = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.CHECK_CIRCLE,
                        size=64,
                        color=ft.Colors.GREEN,
                    ),
                    ft.Text(
                        "Cleanup Complete",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text("Files Deleted", size=14),
                                    self.deleted_count_text,
                                ],
                                horizontal_alignment=(ft.CrossAxisAlignment.CENTER),
                            ),
                            ft.VerticalDivider(width=40),
                            ft.Column(
                                [
                                    ft.Text("Space Saved", size=14),
                                    self.space_saved_text,
                                ],
                                horizontal_alignment=(ft.CrossAxisAlignment.CENTER),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            padding=30,
        )

        # Deleted files list
        deleted_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Deleted Files",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Container(
                        content=self.deleted_files_column,
                        height=150,
                        border=ft.border.all(1, ft.Colors.GREY_400),
                        border_radius=8,
                        padding=10,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(left=20, right=20),
        )

        # Failed files section
        self.failed_section = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.WARNING,
                                color=ft.Colors.ORANGE,
                            ),
                            ft.Text(
                                "Failed to Delete",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            self.failed_count_text,
                        ],
                        spacing=10,
                    ),
                    ft.Container(
                        content=self.failed_files_column,
                        height=100,
                        border=ft.border.all(1, ft.Colors.ORANGE_200),
                        border_radius=8,
                        padding=10,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(left=20, right=20),
            visible=False,
        )

        return ft.Column(
            [
                success_section,
                ft.Divider(),
                deleted_section,
                self.failed_section,
                ft.Divider(),
                ft.Container(
                    content=ft.Row(
                        [
                            self.back_to_home_button,
                            self.done_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=20,
                    ),
                    alignment=ft.alignment.center,
                    padding=20,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
            expand=True,
        )

    def set_result(self, result: DeleteResult) -> None:
        """
        Set the delete result and update the UI.

        Args:
            result: The delete operation result.
        """
        self.delete_result = result

        # Update summary texts
        self.deleted_count_text.value = str(result.total_deleted)
        self.space_saved_text.value = Deleter.format_size(result.space_saved)
        self.failed_count_text.value = str(result.total_failed)

        # Update deleted files list
        self.deleted_files_column.controls.clear()
        for file_path in result.deleted_files:
            self.deleted_files_column.controls.append(
                ft.Text(file_path, size=12, color=ft.Colors.GREY_700)
            )

        # Update failed files list
        self.failed_files_column.controls.clear()
        for file_path, error in result.failed_files:
            self.failed_files_column.controls.append(
                ft.Column(
                    [
                        ft.Text(file_path, size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(error, size=11, color=ft.Colors.RED_400),
                    ],
                    spacing=2,
                )
            )

        # Show/hide failed section
        self.failed_section.visible = result.total_failed > 0

        if self.page:
            self.page.update()

    def set_done_callback(self, callback: Callable[[], None]) -> None:
        """
        Set the callback for when done button is clicked.

        Args:
            callback: Function to call when done.
        """
        self.done_callback = callback

    def set_back_to_home_callback(self, callback: Callable[[], None]) -> None:
        """
        Set the callback for when back to home button is clicked.

        Args:
            callback: Function to call when back to home.
        """
        self.back_to_home_callback = callback

    def _on_done_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """Handle done button click."""
        if self.done_callback:
            self.done_callback()

    def _on_back_to_home_clicked(self, e: Optional[ft.ControlEvent]) -> None:
        """Handle back to home button click."""
        if self.back_to_home_callback:
            self.back_to_home_callback()
