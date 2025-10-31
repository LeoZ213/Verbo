"""Utilities for extracting book covers from different file formats."""

import tempfile
import io
from pdf2image import convert_from_path
from ebooklib import epub
from PIL import Image


def get_pdf_cover(file_path: str) -> str:
    """
    Extract the first page of a PDF as a cover image.

    Args:
        file_path: Path to the PDF file

    Returns:
        Path to the temporary PNG file containing the cover
    """
    pdf_pages = convert_from_path(file_path, first_page=1, last_page=1)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pdf_pages[0].save(tmp.name, format="PNG")
    return tmp.name


def get_epub_cover(file_path: str) -> str | None:
    """
    Extract the cover image from an EPUB file.

    Args:
        file_path: Path to the EPUB file

    Returns:
        Path to the temporary PNG file containing the cover, or None if no cover found
    """
    try:
        book = epub.read_epub(file_path)
        cover_image = book.get_item_with_id('cover-image')

        if cover_image:
            img = Image.open(io.BytesIO(cover_image.get_content()))
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            img.save(tmp.name, format="PNG")
            return tmp.name
    except Exception as e:
        print(f"Error extracting EPUB cover: {e}")

    return None