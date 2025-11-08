import flet as ft
import fitz
import tempfile
import os


def render_pdf_content(file_path: str) -> ft.Container:
    """
    Create a PDF viewer with navigation support.

    Args:
        file_path: Path to the PDF file

    Returns:
        Container with the PDF viewer
    """
    # Open PDF
    pdf_document = fitz.open(file_path)
    total_pages = len(pdf_document)

    # Create temp directory
    temp_dir = tempfile.mkdtemp()

    # Current page state
    current_page = [0]  # Using list to maintain reference

    # Create image widget
    page_image = ft.Image(
        fit=ft.ImageFit.CONTAIN,
        expand=True,
    )

    # Current page number text
    page_info = ft.Text(
        f"Page {current_page[0] + 1} of {total_pages}",
        color=ft.Colors.BLACK
    )

    def render_page(page_num):
        """Render a specific page."""
        pdf_page = pdf_document[page_num]
        pix = pdf_page.get_pixmap()

        img_path = os.path.join(temp_dir, f"page_{page_num}.png")
        pix.save(img_path)

        page_image.src = os.path.abspath(img_path)
        if page_image.page:
            page_image.update()

    def next_page(e):
        """Navigate to next page."""
        if current_page[0] < total_pages - 1:
            current_page[0] += 1
            render_page(current_page[0])

            # Updates the page number text
            page_info.value = f"Page {current_page[0] + 1} of {total_pages}"
            page_info.update()

    def prev_page(e):
        """Navigate to previous page."""
        if current_page[0] > 0:
            current_page[0] -= 1
            render_page(current_page[0])

            # Updates the page number text
            page_info.value = f"Page {current_page[0] + 1} of {total_pages}"
            page_info.update()

    # Create toolbar
    toolbar = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("Previous", on_click=prev_page),
            ft.ElevatedButton("Next", on_click=next_page),
            page_info
        ]),
        padding=10,
        bgcolor=ft.Colors.INVERSE_SURFACE,
    )

    # Render first page
    render_page(0)

    # Return complete viewer with toolbar
    return ft.Container(
        content=ft.Column([
            toolbar,
            ft.Container(
                content=page_image,
                expand=True,
                alignment=ft.alignment.center,
            ),
        ], spacing=0, expand=True),
        expand=True,
    )


def render_epub_content(file_path: str):
    return

def render_txt_content(file_path: str) -> ft.Container:
    """
    Create a simple TXT file reader widget.

    Args:
        file_path: Path to the TXT file

    Returns:
        Container with the TXT reader interface
    """
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # Fallback to different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            content = f"Error reading file: {str(e)}"
    except Exception as e:
        content = f"Error reading file: {str(e)}"

    # Create scrollable text display
    text_display = ft.TextField(
        value=content,
        multiline=True,
        read_only=True,
        border=ft.InputBorder.NONE,
        text_size=16,
        expand=True,
        # Allow text selection for copying
        selection_color=ft.Colors.BLUE_200,
    )

    # Wrap in a container with padding
    reader_container = ft.Container(
        content=ft.Column(
            [text_display],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        padding=20,
        expand=True,
        bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
    )

    return reader_container

def handle_text_selection():
    return

def add_annotation():
    return

def translated_selected_text():
    return

