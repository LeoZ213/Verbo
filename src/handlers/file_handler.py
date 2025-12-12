"""Handlers for file operations (picking, adding to library/grid)."""

import flet as ft
from flet.core.file_picker import FilePickerFile
from flet.core.grid_view import GridView

from src.utils.cover_extractor import get_pdf_cover
from src.ui.main_page_ui import create_book_cover_widget, create_book_item
from src.handlers.book_handler import book_item_double_tap
from src.handlers.database_handler import DatabaseHandler

def add_to_library(file: FilePickerFile, library_list: ft.ListView):
    """
    Add selected file to the Library list.

    Args:
        file: Selected file from file picker
        library_list: ListView to add the file to

    Returns:
        The created library item control
    """
    library_item = ft.TextButton(
        content=ft.Text(file.name, max_lines=1, color=ft.Colors.ON_SURFACE),
        style=ft.ButtonStyle(
            padding=ft.padding.symmetric(horizontal=20),
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
        ),
        data={'path': file.path, 'name': file.name}
    )
    library_list.controls.append(library_item)
    library_list.update()
    return library_item


def add_to_grid(file: FilePickerFile, book_grid: GridView, tabs_list: ft.Tabs,
                library_list: ft.ListView, db: DatabaseHandler):
    """
    Add a book to the grid view with appropriate cover.

    Args:
        file: Selected file from file picker
        book_grid: GridView to add the book to
        tabs_list: Tabs list for book opening functionality
        library_list: ListView for library items
        db: Database handler for persistence
    """
    file_ext = file.name.rsplit(".", 1)[-1].lower()
    print(f"Adding {file.name} with extension: {file_ext}")

    # Check if book already exists in database
    if db.book_exists(file.path):
        print(f"Book already exists: {file.name}")
        return

    cover_path = None

    # Extract cover based on file type
    if file_ext == "pdf":
        cover_path = get_pdf_cover(file.path)
    elif file_ext == "txt":
        pass  # Will use default icon
    else:
        print(f"Unsupported file type: {file_ext}")
        return

    # Create cover widget
    cover_widget = create_book_cover_widget(file_ext, cover_path)

    # Add to library first and get the library item reference
    library_item = add_to_library(file, library_list)

    # Add to database
    db.add_book(file.name, file.path, file_ext)

    # Create remove handler
    def remove_book(e):
        # Get book_data from the closure (file object)
        book_data = {'path': file.path, 'name': file.name, 'ext': file_ext}

        # Remove from database
        db.remove_book(book_data['path'])

        # Remove from grid
        for item in book_grid.controls[:]:
            if item.data and item.data['path'] == book_data['path']:
                book_grid.controls.remove(item)
        book_grid.update()

        # Remove from library
        for item in library_list.controls[:]:
            if hasattr(item, 'data') and item.data and item.data['path'] == book_data['path']:
                library_list.controls.remove(item)
        library_list.update()

    # Create book item with double-tap handler and remove handler
    book_item = create_book_item(
        file.path,
        file.name,
        file_ext,
        cover_widget,
        lambda e: book_item_double_tap(e, tabs_list),
        remove_book
    )

    book_grid.controls.append(book_item)
    book_grid.update()


def load_books_from_database(db: DatabaseHandler, book_grid: GridView,
                             tabs_list: ft.Tabs, library_list: ft.ListView):
    """
    Load all books from database on application startup.

    Args:
        db: Database handler
        book_grid: GridView to add books to
        tabs_list: Tabs list for book opening functionality
        library_list: ListView for library items
    """
    books = db.get_all_books()

    for book_data in books:
        file_ext = book_data['ext']
        file_path = book_data['path']
        file_name = book_data['name']

        cover_path = None

        # Extract cover based on file type
        if file_ext == "pdf":
            cover_path = get_pdf_cover(file_path)
        elif file_ext == "txt":
            pass  # Will use default icon

        # Create cover widget
        cover_widget = create_book_cover_widget(file_ext, cover_path)

        # Add to library
        library_item = ft.TextButton(
            content=ft.Text(file_name, max_lines=1, color=ft.Colors.ON_SURFACE),
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=20),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.AMBER),
            ),
            data={'path': file_path, 'name': file_name}
        )
        library_list.controls.append(library_item)

        # Create remove handler
        def remove_book(e, book_data=book_data):
            # Remove from database
            db.remove_book(book_data['path'])

            # Remove from grid
            for item in book_grid.controls[:]:
                if item.data and item.data['path'] == book_data['path']:
                    book_grid.controls.remove(item)
            book_grid.update()

            # Remove from library
            for item in library_list.controls[:]:
                if hasattr(item, 'data') and item.data and item.data['path'] == book_data['path']:
                    library_list.controls.remove(item)
            library_list.update()

        # Create book item
        book_item = create_book_item(
            file_path,
            file_name,
            file_ext,
            cover_widget,
            lambda e, bd=book_data: book_item_double_tap(e, tabs_list),
            remove_book
        )

        book_grid.controls.append(book_item)

    # Update UI after loading all books
    book_grid.update()
    library_list.update()


def on_dialogue_result(e: ft.FilePickerResultEvent, library_list: ft.ListView,
                       book_grid: GridView, tabs_list: ft.Tabs, db: DatabaseHandler):
    """
    Handle file picker result event.

    Args:
        e: File picker result event
        library_list: ListView for library items
        book_grid: GridView for book display
        tabs_list: Tabs list for book opening
        db: Database handler for persistence
    """
    if e.files:
        for f in e.files:
            print(f"Selected file: {f.name}")
            add_to_grid(f, book_grid, tabs_list, library_list, db)
    else:
        print("No file selected")