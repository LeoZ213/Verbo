"""Handlers for book interactions (opening, searching, tabs)."""

import flet as ft

from src.handlers.reader_handler import render_txt_content, render_pdf_content

def create_book_tab(book_data: dict) -> ft.Tab:
    """
    Create a new tab for a book.

    Args:
        book_data: Dictionary containing book info (name, path, ext)

    Returns:
        Tab object for the book
    """

    book_content = None

    if book_data['ext'] == "txt":
        book_content = render_txt_content(book_data['path'])
    elif book_data['ext'] == "pdf":
        book_content = render_pdf_content(book_data['path'])
    elif book_data['ext'] == "epub":
        #TODO Convert EPUB to a readable format
        print("epub not converted to readable format yet")

    return ft.Tab(
        text=book_data['name'][0:5],
        content=ft.Column(
            controls=[
                book_content,
            ]
        )
        # TODO: Wrap the text or have a hard border
    )

def book_item_double_tap(e: ft.ControlEvent, tabs_list: ft.Tabs):
    """
    Handle double-tap on a book item - opens it in a new tab.

    Args:
        e: Control event containing book data
        tabs_list: Tabs widget to add the new tab to
    """
    book_data = e.control.data
    print(f"Opening: {book_data['name']}")
    print(f"Path: {book_data['path']}")

    tabs_list.tabs.append(create_book_tab(book_data))
    tabs_list.selected_index = len(tabs_list.tabs) - 1
    tabs_list.update()


def search_books(e: ft.ControlEvent, book_grid: ft.GridView):
    """
    Filter books in the grid based on search query.

    Args:
        e: Control event containing search query
        book_grid: GridView containing book items
    """
    query = e.control.value.lower().strip()

    # If search is empty, show all books
    if not query:
        for book_item in book_grid.controls:
            book_item.visible = True
    else:
        # Hide books that don't match the search
        for book_item in book_grid.controls:
            # Get the book name from the Text widget (second control in Column)
            book_name = book_item.content.controls[1].value.lower()
            book_item.visible = query in book_name

    book_grid.update()


