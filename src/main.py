"""Duplicate file scanner application built with Flet."""

import flet as ft


def main(page: ft.Page) -> None:
    """Main entry point for the Flet application.

    Args:
        page: The Flet page instance
    """
    page.title = "Duplicate File Scanner"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def button_clicked(e):
        """Handle button click event."""
        text_field.value = "Hello, Flet!"
        page.update()

    text_field = ft.Text(value="Welcome to Duplicate File Scanner", size=30)
    button = ft.ElevatedButton(text="Click me", on_click=button_clicked)

    page.add(
        ft.Column(
            [
                text_field,
                button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
