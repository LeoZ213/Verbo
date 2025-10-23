import flet as ft
import tempfile
import io

from flet.core.file_picker import FilePickerFile
from flet.core.grid_view import GridView
from pdf2image import convert_from_path
from ebooklib import epub
from PIL import Image


# Event Handlers
def handle_change(e: ft.ControlEvent):
    """Triggered when expansion panel changes"""
    print(f"Change on panel with index {e.data}")

def get_epub_cover_with_lib(file_path):
    book = epub.read_epub(file_path)
    cover_image = book.get_item_with_id('cover-image')  # or search for cover
    if cover_image:
        return Image.open(io.BytesIO(cover_image.get_content()))
    return None # Return none if no cover were found

def add_to_library(file: FilePickerFile, library_list: ft.ListView):
    """Add selected file to the Library list"""
    file_name = file.name.rsplit(".", 1)[0]  # remove extension
    library_list.controls.append(
        ft.TextButton(
            content=ft.Text(file_name, max_lines=1),
            style=ft.ButtonStyle(
                color=ft.Colors.RED,
                padding=ft.padding.symmetric(horizontal=20),
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.RED),
            ),
        )
    )
    library_list.update()

def add_to_grid(file: FilePickerFile, book_grid: GridView):

    # Get file extension
    file_ext = file.name.rsplit(".", 1)[-1]
    file_name = file.name.rsplit(".", 1)[0] # Get file name without the extension
    print(file_ext)

    book_cover = None

    if file_ext == "pdf":
        # Convert the first page of the PDF to an image
        pdf_pages = convert_from_path(file.path, first_page=1, last_page=1)
        # Save as temporary png
        tmp = tempfile.NamedTemporaryFile(suffix = ".png", delete=False)
        pdf_pages[0].save(tmp.name, format="PNG")

        book_cover = ft.Image(src=tmp.name, width=150, height=200, fit=ft.ImageFit.CONTAIN)
    elif file_ext == "epub":
        epub_cover = get_epub_cover_with_lib(file.path)
        print(epub_cover)
        if epub_cover:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            epub_cover.save(tmp.name, format="PNG")
            book_cover = ft.Image(src=tmp.name, width=150, height=200, fit=ft.ImageFit.CONTAIN)
        else:
            # Fallback to icon or placeholder
            book_cover = ft.Icon(ft.Icons.BOOK, size=150)
    elif file_ext == "txt":
        # Generic Icon for txt placeholder
        book_cover = ft.Icon(ft.Icons.DESCRIPTION, size=150)
    else:
        print("Unsupported file type")
        return

    # Makes sure the icons are in the same size
    book_cover_container = ft.Container(
        content=book_cover,
        width=150,
        height=200,
        alignment=ft.alignment.center
    )

    book_item = ft.Column(
        controls=[
            book_cover_container,
            ft.Text(
                file_name,
                size = 12,
                weight=ft.FontWeight.NORMAL,
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
                width=150,
                color=ft.Colors.BLACK
            )
        ],
        #horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        #alignment=ft.MainAxisAlignment.CENTER
    )
    book_grid.controls.append(book_item)

    book_grid.update()

def on_dialogue_result(e: ft.FilePickerResultEvent, library_list: ft.ListView, book_grid: GridView):
    """Handle file picker result event"""
    if e.files:
        for f in e.files:
            print(f"Selected file: {f.name}")
            add_to_library(f, library_list)
            add_to_grid(f, book_grid)
    else:
        print("No file selected")


# UI Builders
def build_left_panel(library_list: ft.ListView, table_list: ft.ListView):
    """Builds the left sidebar with library and TOC panels"""
    return ft.ExpansionPanelList(
        expand_icon_color=ft.Colors.AMBER,
        elevation=8,
        divider_color=ft.Colors.AMBER,
        on_change=handle_change,
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

def build_book_grid():
    """Builds the main book display grid"""
    return ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=150,
        child_aspect_ratio=0.65,
        # Change this to increase/decrease vertical space between rows
        spacing=30,
        # Change this to increase/decrease horizontal spacing between child
        run_spacing=5,
    )


def search_books(e: ft.ControlEvent, book_grid: GridView):
    """Filter books based on search query"""
    query = e.control.value.lower().strip()

    # If search is empty, show all books
    if not query:
        for book_item in book_grid.controls:
            book_item.visible = True
    else:
        # Hide books that don't match the search
        for book_item in book_grid.controls:
            # Get the book name from the Text widget (second control in Column)
            book_name = book_item.controls[1].value.lower()

            if query in book_name:
                book_item.visible = True
            else:
                book_item.visible = False

    book_grid.update()

# Main App
def main(page: ft.Page):
    # Page setup
    page.title = "Main Page"
    page.bgcolor = ft.Colors.WHITE

    # UI Components
    library_list = ft.ListView(height=page.height / 2)
    table_list = ft.ListView(height=page.height / 2)
    left_panel = build_left_panel(library_list, table_list)
    book_grid = build_book_grid()

    # Search bar and file picker
    file_extensions = ["pdf", "txt", "epub"]
    file_picker = ft.FilePicker(on_result=lambda e: on_dialogue_result(e, library_list, book_grid))
    choose_button = ft.FloatingActionButton(
        icon=ft.Icons.ADD,
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=True, allowed_extensions=file_extensions
        ),
    )
    book_search = ft.SearchBar(
        view_elevation=4,
        divider_color=ft.Colors.AMBER,
        bar_hint_text="Search for books...",
        on_change=lambda e: search_books(e, book_grid)
    )

    page.overlay.append(file_picker)

    # Layout
    layout = ft.Row(
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

    page.add(layout)
    page.update()

ft.app(target=main)