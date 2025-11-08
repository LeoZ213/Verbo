"""Main application entry point."""

import flet as ft

from ui.main_page_ui import build_left_panel, build_book_grid
from handlers.file_handler import on_dialogue_result
from handlers.book_handler import search_books


def main(page: ft.Page):
    """Initialize and run the book library application."""
    # Page setup
    page.title = "Book Library"
    page.bgcolor = ft.Colors.WHITE
    page.theme = ft.Theme(
        text_theme=ft.TextTheme(
            # This styles the main paragraph text
            body_medium=ft.TextStyle(color=ft.Colors.BLACK, size=16),

            # This styles '#' (H1) text, like your "Contents"
            headline_small=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD, size=24),

            # This styles '##' (H2) text
            title_large=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD, size=22),

            # This styles '###' (H3) text
            title_medium=ft.TextStyle(color=ft.Colors.BLACK, weight=ft.FontWeight.BOLD, size=20),
        )
    )

    # Create UI components
    library_list = ft.ListView(height=page.height / 2)
    table_list = ft.ListView(height=page.height / 2)
    left_panel = build_left_panel(library_list, table_list)
    book_grid = build_book_grid()

    # Create tabs
    tabs_list = ft.Tabs(
        animation_duration=300,
        tabs=[ft.Tab(text="Main page")],
        # Used to make sure the tab isn't 0px so images render
        expand=True
    )

    # File picker setup
    file_extensions = ["pdf", "txt", "epub"]
    file_picker = ft.FilePicker(
        on_result=lambda e: on_dialogue_result(e, library_list, book_grid, tabs_list)
    )
    page.overlay.append(file_picker)

    # Action buttons
    choose_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=file_extensions
        ),
    )

    book_search = ft.SearchBar(
        view_elevation=4,
        divider_color=ft.Colors.AMBER,
        bar_hint_text="Search for books...",
        on_change=lambda e: search_books(e, book_grid)
    )

    # Build main layout
    main_page = ft.Row(
        expand=True,
        vertical_alignment=ft.CrossAxisAlignment.START,
        controls=[
            # Left sidebar
            ft.Container(
                expand=1,
                content=ft.ListView(expand=True, controls=[left_panel], spacing=10),
            ),
            # Main content area
            ft.Column(
                expand=3,
                controls=[
                    ft.Row(controls=[book_search, choose_button]),
                    ft.Container(content=book_grid, expand=True),
                ],
            ),
        ],
    )

    tabs_list.tabs[0].content = main_page
    page.add(tabs_list)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)