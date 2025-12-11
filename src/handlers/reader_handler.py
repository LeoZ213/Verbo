import ebooklib
import flet as ft
import fitz
import tempfile
import os
from bs4 import BeautifulSoup
from ebooklib import epub
from abc import ABC, abstractmethod


class BookReader(ABC):
    """Base class for all book readers"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.current_position = 0

    @abstractmethod
    def load(self):
        """Load the book file"""
        pass

    @abstractmethod
    def get_content(self, position: int):
        """Get content at a specific position"""
        pass

    @abstractmethod
    def get_total_items(self) -> int:
        """Get total number of pages/chapters"""
        pass

    @abstractmethod
    def render(self) -> ft.Container:
        """Render the reader UI"""
        pass


class PDFReader(BookReader):
    """PDF book reader"""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.document = None
        self.temp_dir = None

    def load(self):
        """Load the PDF document"""
        self.document = fitz.open(self.file_path)
        self.temp_dir = tempfile.mkdtemp()

    def get_content(self, position: int):
        """Render a PDF page to an image"""
        if not self.document:
            return None

        page = self.document[position]
        pix = page.get_pixmap()
        img_path = os.path.join(self.temp_dir, f"page_{position}.png")
        pix.save(img_path)
        return os.path.abspath(img_path)

    def get_total_items(self) -> int:
        return len(self.document) if self.document else 0

    def render(self) -> ft.Container:
        """Render PDF reader UI"""
        self.load()

        # UI Components
        page_image = ft.Image(fit=ft.ImageFit.CONTAIN, expand=True)
        page_info = ft.Text(f"Page 1 of {self.get_total_items()}", color=ft.Colors.BLACK)

        def update_page():
            img_path = self.get_content(self.current_position)
            page_image.src = img_path
            page_info.value = f"Page {self.current_position + 1} of {self.get_total_items()}"
            if page_image.page:
                page_image.update()
                page_info.update()

        def next_page(e):
            if self.current_position < self.get_total_items() - 1:
                self.current_position += 1
                update_page()

        def prev_page(e):
            if self.current_position > 0:
                self.current_position -= 1
                update_page()

        # Initialize
        update_page()

        # Build UI
        toolbar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("Previous", on_click=prev_page),
                ft.ElevatedButton("Next", on_click=next_page),
                page_info
            ]),
            padding=10,
            bgcolor=ft.Colors.INVERSE_SURFACE,
        )

        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Container(content=page_image, expand=True, alignment=ft.alignment.center),
            ], spacing=0, expand=True),
            expand=True,
        )


class EPUBReader(BookReader):
    """EPUB book reader"""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.book = None
        self.chapters = []
        self.title = "Unknown Title"
        self.author = "Unknown Author"

    def load(self):
        """Load the EPUB file"""
        self.book = epub.read_epub(self.file_path)
        self.chapters = [item for item in self.book.get_items()
                         if item.get_type() == ebooklib.ITEM_DOCUMENT]

        # Extract metadata
        title_meta = self.book.get_metadata('DC', 'title')
        author_meta = self.book.get_metadata('DC', 'creator')
        self.title = title_meta[0][0] if title_meta else "Unknown Title"
        self.author = author_meta[0][0] if author_meta else "Unknown Author"

    def get_content(self, position: int) -> str:
        """Get chapter text"""
        if not self.chapters or position >= len(self.chapters):
            return "No content available"

        soup = BeautifulSoup(self.chapters[position].get_content(), 'html.parser')

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Convert HTML tags for basic formatting
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            level = int(tag.name[1])
            tag.string = '#' * level + ' ' + tag.get_text()

        for tag in soup.find_all('em'):
            tag.string = '*' + tag.get_text() + '*'

        for tag in soup.find_all('strong'):
            tag.string = '**' + tag.get_text() + '**'

        for tag in soup.find_all('p'):
            tag.append('\n\n')

        text = soup.get_text()

        # Clean up whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)
            elif cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')

        return '\n'.join(cleaned_lines)

    def get_total_items(self) -> int:
        return len(self.chapters)

    def render(self) -> ft.Container:
        """Render EPUB reader UI"""
        try:
            self.load()
            if not self.chapters:
                return ft.Container(
                    content=ft.Text("No readable content found in EPUB file"),
                    padding=20
                )
        except Exception as e:
            return ft.Container(
                content=ft.Text(f"Error loading EPUB: {str(e)}"),
                padding=20
            )

        # UI Components
        content_display = ft.Markdown(
            value="",
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            expand=True,
        )

        chapter_info = ft.Text(f"Chapter 1 of {self.get_total_items()}", color=ft.Colors.BLACK)
        book_info = ft.Text(
            f"{self.title} by {self.author}",
            color=ft.Colors.BLACK,
            weight=ft.FontWeight.BOLD,
            size=14
        )

        def update_chapter():
            content_display.value = self.get_content(self.current_position)
            chapter_info.value = f"Chapter {self.current_position + 1} of {self.get_total_items()}"
            if content_display.page:
                content_display.update()
                chapter_info.update()

        def next_chapter(e):
            if self.current_position < self.get_total_items() - 1:
                self.current_position += 1
                update_chapter()

        def prev_chapter(e):
            if self.current_position > 0:
                self.current_position -= 1
                update_chapter()

        # Initialize
        update_chapter()

        # Build UI
        toolbar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("Previous", on_click=prev_chapter),
                ft.ElevatedButton("Next", on_click=next_chapter),
                chapter_info,
                ft.Container(expand=True),
                book_info,
            ]),
            padding=10,
            bgcolor=ft.Colors.INVERSE_SURFACE,
        )

        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Container(
                    content=ft.Container(
                        content=content_display,
                        padding=20,
                        bgcolor=ft.Colors.WHITE,
                    ),
                    expand=True,
                ),
            ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO),
            expand=True,

        )


class TXTReader(BookReader):
    """Plain text file reader"""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.content = ""

    def load(self):
        """Load the text file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
        except UnicodeDecodeError:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                self.content = f.read()

    def get_content(self, position: int = 0) -> str:
        return self.content

    def get_total_items(self) -> int:
        return 1  # Single page for text files

    def render(self) -> ft.Container:
        """Render text reader UI"""
        try:
            self.load()
        except Exception as e:
            return ft.Container(
                content=ft.Text(f"Error reading file: {str(e)}"),
                padding=20
            )

        text_display = ft.TextField(
            value=self.content,
            multiline=True,
            read_only=True,
            border=ft.InputBorder.NONE,
            text_size=16,
            expand=True,
            selection_color=ft.Colors.BLUE_200,
            color=ft.Colors.BLACK,
        )

        return ft.Container(
            content=ft.Column([text_display], scroll=ft.ScrollMode.AUTO, expand=True),
            padding=20,
            expand=True,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
        )


# Factory function to create the right reader
def create_reader(file_path: str) -> BookReader:
    """Create appropriate reader based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return PDFReader(file_path)
    elif ext == '.epub':
        return EPUBReader(file_path)
    elif ext == '.txt':
        return TXTReader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# Convenience functions for backward compatibility
def render_pdf_content(file_path: str) -> ft.Container:
    return PDFReader(file_path).render()


def render_epub_content(file_path: str) -> ft.Container:
    return EPUBReader(file_path).render()


def render_txt_content(file_path: str) -> ft.Container:
    return TXTReader(file_path).render()