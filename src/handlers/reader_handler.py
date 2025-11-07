import flet as ft
import fitz
import tempfile
import os


def render_pdf_content(file_path: str) -> ft.Container:
    """
    Create a simple PDF viewer showing the first page.

    Args:
        file_path: Path to the PDF file

    Returns:
        Container with the PDF image
    """
    # Open PDF
    pdf_document = fitz.open(file_path)

    # Create temp directory for page images
    temp_dir = tempfile.mkdtemp()

    # Get first page
    pdf_page = pdf_document[0]

    # Render page to image
    pix = pdf_page.get_pixmap()

    # Save to temp file
    #TODO Change the temp file name depending on the page
    img_path = os.path.join(temp_dir, f"page_0.png")
    pix.save(img_path)

    # Create image
    page_image = ft.Image(
        src=os.path.abspath(img_path),
        fit=ft.ImageFit.CONTAIN,
    )

    # Return in a container
    return ft.Container(
        content=page_image,
        expand=True,
        alignment=ft.alignment.center,
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

