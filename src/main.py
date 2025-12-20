"""Main application entry point."""

import flet as ft

from ui.main_page_ui import build_left_panel, build_book_grid
from handlers.file_handler import on_dialogue_result, load_books_from_database
from handlers.book_handler import search_books
from handlers.database_handler import DatabaseHandler


def main(page: ft.Page):
    """Initialize and run the book library application."""
    print("\n" + "="*60)
    print("[DEBUG] Starting Book Library Application")
    print("="*60 + "\n")

    # Page setup
    page.title = "Book Library"
    page.bgcolor = ft.Colors.GREY_50  # Softer light background
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.icon = "icon.ico"
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.AMBER,
        text_theme=ft.TextTheme(
            # This styles the main paragraph text
            body_medium=ft.TextStyle(color=ft.Colors.GREY_900, size=16),

            # This styles '#' (H1) text, like your "Contents"
            headline_small=ft.TextStyle(color=ft.Colors.GREY_900, weight=ft.FontWeight.BOLD, size=24),

            # This styles '##' (H2) text
            title_large=ft.TextStyle(color=ft.Colors.GREY_900, weight=ft.FontWeight.BOLD, size=22),

            # This styles '###' (H3) text
            title_medium=ft.TextStyle(color=ft.Colors.GREY_900, weight=ft.FontWeight.BOLD, size=20),
        )
    )

    # Initialize database
    print("[DEBUG] Initializing database...")
    db = DatabaseHandler()

    # Print current database contents
    db.print_all_books_raw()

    # Create UI components
    library_list = ft.ListView(expand=True)
    left_panel = build_left_panel(library_list)
    book_grid = build_book_grid()

    # Create tabs
    tabs_list = ft.Tabs(
        animation_duration=300,
        tabs=[ft.Tab(text="Main page")],
        # Used to make sure the tab isn't 0 px so images render
        expand=True
    )

    # File picker setup
    file_extensions = ["pdf", "txt"]
    file_picker = ft.FilePicker(
        on_result=lambda e: on_dialogue_result(e, library_list, book_grid, tabs_list, db)
    )
    page.overlay.append(file_picker)

    # Theme toggle button
    def toggle_theme(e):
        if page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.DARK
            page.bgcolor = ft.Colors.GREY_900  # Softer dark background
            theme_button.icon = ft.Icons.LIGHT_MODE
            theme_button.tooltip = "Switch to Light Mode"
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
            page.bgcolor = ft.Colors.GREY_50  # Softer light background
            theme_button.icon = ft.Icons.DARK_MODE
            theme_button.tooltip = "Switch to Dark Mode"

        # Force update of each book item in the grid to refresh text colors
        for item in book_grid.controls:
            # Recursively update all nested controls
            def update_recursive(control):
                if hasattr(control, 'update'):
                    control.update()
                if hasattr(control, 'content'):
                    if isinstance(control.content, list):
                        for c in control.content:
                            update_recursive(c)
                    elif control.content:
                        update_recursive(control.content)
                if hasattr(control, 'controls'):
                    for c in control.controls:
                        update_recursive(c)

            update_recursive(item)

        page.update()

    theme_button = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        tooltip="Switch to Dark Mode",
        on_click=toggle_theme,
    )

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
        on_change=lambda e: search_books(e, book_grid),
        expand=True,
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
                    ft.Row(controls=[book_search, theme_button, choose_button]),
                    ft.Container(content=book_grid, expand=True),
                ],
            ),
        ],
    )

    tabs_list.tabs[0].content = main_page
    page.add(tabs_list)

    # Load books from database after UI is set up
    print("[DEBUG] Loading books from database...")
    load_books_from_database(db, book_grid, tabs_list, library_list)
    print(f"[DEBUG] Book grid now has {len(book_grid.controls)} items")

    page.update()

    print("\n[DEBUG] Application startup complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")