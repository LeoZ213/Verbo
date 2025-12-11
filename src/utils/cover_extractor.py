"""Utilities for extracting book covers from different file formats."""

import tempfile
from pdf2image import convert_from_path

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
