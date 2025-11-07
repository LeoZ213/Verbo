"""Reusable UI component builders."""

import flet as ft


def build_left_panel(library_list: ft.ListView, table_list: ft.ListView) -> ft.ExpansionPanelList:
    """
    Builds the left sidebar with library and TOC panels.

    Args:
        library_list: ListView containing library items
        table_list: ListView containing table of contents items

    Returns:
        ExpansionPanelList containing both panels
    """
    return ft.ExpansionPanelList(
        expand_icon_color=ft.Colors.AMBER,
        elevation=8,
        divider_color=ft.Colors.AMBER,
        controls=[
            ft.ExpansionPanel(
                bgcolor=ft.Colors.WHITE,
                header=ft.ListTile(
                    title=ft.Text("Library"),
                    bgcolor=ft.Colors.WHITE,
                    text_color=ft.Colors.BLACK,
                ),
                content=library_list,
            ),
            ft.ExpansionPanel(
                bgcolor=ft.Colors.WHITE,
                header=ft.ListTile(
                    title=ft.Text("Table of Contents"),
                    bgcolor=ft.Colors.WHITE,
                    text_color=ft.Colors.BLACK,
                ),
                content=table_list,
            ),
        ],
    )


def build_book_grid() -> ft.GridView:
    """
    Builds the main book display grid.

    Returns:
        GridView configured for book display
    """
    return ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=150,
        child_aspect_ratio=0.65,
        spacing=30,
        run_spacing=5,
    )


def create_book_cover_widget(file_ext: str, cover_path: str | None) -> ft.Control:
    """
    Create appropriate cover widget based on file type.

    Args:
        file_ext: File extension (pdf, epub, txt, etc.)
        cover_path: Path to cover image, or None for placeholder

    Returns:
        Flet control representing the book cover
    """
    if cover_path:
        return ft.Image(
            src=cover_path,
            width=150,
            height=200,
            fit=ft.ImageFit.CONTAIN
        )

    # Fallback icons based on file type
    if file_ext == "epub":
        return ft.Icon(ft.Icons.BOOK, size=150)
    elif file_ext == "txt":
        return ft.Icon(ft.Icons.DESCRIPTION, size=150)
    else:
        return ft.Icon(ft.Icons.BOOK, size=150)


def create_book_item(file_path: str, file_name: str, file_ext: str,
                     cover_widget: ft.Control, on_double_tap_handler) -> ft.GestureDetector:
    """
    Create a book item for the grid view.

    Args:
        file_path: Full path to the book file
        file_name: Display name of the book
        file_ext: File extension
        cover_widget: Widget displaying the book cover
        on_double_tap_handler: Callback for double-tap events

    Returns:
        GestureDetector containing the complete book item
    """
    book_data = {'path': file_path, 'name': file_name, 'ext': file_ext}

    book_cover_container = ft.Container(
        content=cover_widget,
        data=book_data,
        width=150,
        height=200,
        alignment=ft.alignment.center,
    )

    return ft.GestureDetector(
        content=ft.Column(
            controls=[
                book_cover_container,
                ft.Text(
                    file_name.rsplit(".", 1)[0],  # Remove extension
                    size=12,
                    weight=ft.FontWeight.NORMAL,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    width=150,
                    color=ft.Colors.BLACK
                )
            ],
        ),
        on_double_tap=on_double_tap_handler,
        data=book_data,
    )