"""Handlers for file operations (picking, adding to library/grid)."""

import flet as ft
from flet.core.file_picker import FilePickerFile
from flet.core.grid_view import GridView

from src.utils.cover_extractor import get_pdf_cover, get_epub_cover
from src.ui.main_page_ui import create_book_cover_widget, create_book_item
from src.handlers.book_handler import book_item_double_tap

def add_to_library(file: FilePickerFile, library_list: ft.ListView):
    """
    Add selected file to the Library list.

    Args:
        file: Selected file from file picker
        library_list: ListView to add the file to
    """
    library_list.controls.append(
        ft.TextButton(
            content=ft.Text(file.name, max_lines=1),
            style=ft.ButtonStyle(
                color=ft.Colors.RED,
                padding=ft.padding.symmetric(horizontal=20),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.RED),
            ),
        )
    )
    library_list.update()


def add_to_grid(file: FilePickerFile, book_grid: GridView, tabs_list: ft.Tabs):
    """
    Add a book to the grid view with appropriate cover.

    Args:
        file: Selected file from file picker
        book_grid: GridView to add the book to
        tabs_list: Tabs list for book opening functionality
    """
    file_ext = file.name.rsplit(".", 1)[-1].lower()
    print(f"Adding {file.name} with extension: {file_ext}")

    cover_path = None

    # Extract cover based on file type
    if file_ext == "pdf":
        cover_path = get_pdf_cover(file.path)
    elif file_ext == "epub":
        cover_path = get_epub_cover(file.path)
        print(f"EPUB cover path: {cover_path}")
    elif file_ext == "txt":
        pass  # Will use default icon
    else:
        print(f"Unsupported file type: {file_ext}")
        return

    # Create cover widget
    cover_widget = create_book_cover_widget(file_ext, cover_path)

    # Create book item with double-tap handler
    book_item = create_book_item(
        file.path,
        file.name,
        file_ext,
        cover_widget,
        lambda e: book_item_double_tap(e, tabs_list)
    )

    book_grid.controls.append(book_item)
    book_grid.update()

def on_dialogue_result(e: ft.FilePickerResultEvent, library_list: ft.ListView,
                       book_grid: GridView, tabs_list: ft.Tabs):
    """
    Handle file picker result event.

    Args:
        e: File picker result event
        library_list: ListView for library items
        book_grid: GridView for book display
        tabs_list: Tabs list for book opening
    """
    if e.files:
        for f in e.files:
            print(f"Selected file: {f.name}")
            add_to_library(f, library_list)
            add_to_grid(f, book_grid, tabs_list)
    else:
        print("No file selected")