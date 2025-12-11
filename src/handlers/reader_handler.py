import flet as ft
import fitz
import tempfile
import os
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
        self.zoom_level = 1.0

    def load(self):
        """Load the PDF document"""
        self.document = fitz.open(self.file_path)
        self.temp_dir = tempfile.mkdtemp()

    def get_content(self, position: int):
        """Render a PDF page to an image"""
        if not self.document:
            return None

        page = self.document[position]
        # Apply zoom level to the matrix
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(self.temp_dir, f"page_{position}_zoom_{self.zoom_level}.png")
        pix.save(img_path)
        return os.path.abspath(img_path)

    def get_total_items(self) -> int:
        return len(self.document) if self.document else 0

    def render(self) -> ft.Container:
        """Render PDF reader UI"""
        self.load()

        # UI Components with AnimatedSwitcher for smooth transitions
        page_image = ft.Image(fit=ft.ImageFit.NONE, key="img_0")
        page_info = ft.Text(f"Page 1 of {self.get_total_items()}", color=ft.Colors.ON_INVERSE_SURFACE)
        zoom_info = ft.Text(f"Zoom: {int(self.zoom_level * 100)}%", color=ft.Colors.ON_INVERSE_SURFACE)

        # Image counter for forcing re-renders
        img_counter = [0]

        # Use AnimatedSwitcher for smooth transitions
        image_switcher = ft.AnimatedSwitcher(
            page_image,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=150,  # Fast fade
            reverse_duration=150,
            switch_in_curve=ft.AnimationCurve.EASE_IN,
            switch_out_curve=ft.AnimationCurve.EASE_OUT,
        )

        def update_page():
            # Pre-render the new page
            img_path = self.get_content(self.current_position)

            # Update image fit based on zoom
            if self.zoom_level <= 1.0:
                fit_mode = ft.ImageFit.CONTAIN
            else:
                fit_mode = ft.ImageFit.NONE

            # Create new image with unique key to trigger AnimatedSwitcher
            img_counter[0] += 1
            new_image = ft.Image(
                src=img_path,
                fit=fit_mode,
                key=f"img_{img_counter[0]}"
            )

            # Update text info
            page_info.value = f"Page {self.current_position + 1} of {self.get_total_items()}"
            zoom_info.value = f"Zoom: {int(self.zoom_level * 100)}%"

            # Switch to new image with animation
            image_switcher.content = new_image

            # Update UI
            if image_switcher.page:
                image_switcher.page.update()

        def next_page(e):
            if self.current_position < self.get_total_items() - 1:
                self.current_position += 1
                update_page()

        def prev_page(e):
            if self.current_position > 0:
                self.current_position -= 1
                update_page()

        def zoom_in(e):
            if self.zoom_level < 3.0:  # Max zoom 300%
                self.zoom_level += 0.25
                update_page()

        def zoom_out(e):
            if self.zoom_level > 0.5:  # Min zoom 50%
                self.zoom_level -= 0.25
                update_page()

        def reset_zoom(e):
            self.zoom_level = 1.0
            update_page()

        # Initialize
        update_page()

        # Build UI
        toolbar = ft.Container(
            content=ft.Row([
                ft.ElevatedButton("Previous", on_click=prev_page),
                ft.ElevatedButton("Next", on_click=next_page),
                page_info,
                ft.VerticalDivider(),
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, on_click=zoom_out, tooltip="Zoom Out"),
                ft.IconButton(icon=ft.Icons.ZOOM_IN, on_click=zoom_in, tooltip="Zoom In"),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=reset_zoom, tooltip="Reset Zoom"),
                zoom_info,
            ]),
            padding=10,
            bgcolor=ft.Colors.INVERSE_SURFACE,
        )

        # Scrollable container for the image
        scrollable_content = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [image_switcher],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.ALWAYS,
                    )
                ],
                scroll=ft.ScrollMode.ALWAYS,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.alignment.center,
            expand=True,
        )

        return ft.Container(
            content=ft.Column([
                toolbar,
                scrollable_content,
            ], spacing=10, expand=True),
            expand=True,
        )


class TXTReader(BookReader):
    """Plain text file reader"""

    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.content = ""
        self.font_size = 16

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
            text_size=self.font_size,
            expand=True,
            selection_color=ft.Colors.BLUE_200,
            # Remove hardcoded color to use theme colors
        )

        zoom_info = ft.Text(f"Font: {self.font_size}px", color=ft.Colors.ON_INVERSE_SURFACE)

        def zoom_in(e):
            if self.font_size < 32:  # Max font size
                self.font_size += 2
                text_display.text_size = self.font_size
                zoom_info.value = f"Font: {self.font_size}px"
                text_display.update()
                zoom_info.update()

        def zoom_out(e):
            if self.font_size > 8:  # Min font size
                self.font_size -= 2
                text_display.text_size = self.font_size
                zoom_info.value = f"Font: {self.font_size}px"
                text_display.update()
                zoom_info.update()

        def reset_zoom(e):
            self.font_size = 16
            text_display.text_size = self.font_size
            zoom_info.value = f"Font: {self.font_size}px"
            text_display.update()
            zoom_info.update()

        # Toolbar
        toolbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, on_click=zoom_out, tooltip="Decrease Font Size"),
                ft.IconButton(icon=ft.Icons.ZOOM_IN, on_click=zoom_in, tooltip="Increase Font Size"),
                ft.IconButton(icon=ft.Icons.REFRESH, on_click=reset_zoom, tooltip="Reset Font Size"),
                zoom_info,
            ]),
            padding=10,
            bgcolor=ft.Colors.INVERSE_SURFACE,
        )

        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Column([text_display], scroll=ft.ScrollMode.AUTO, expand=True),
            ], spacing=0, expand=True),
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
    elif ext == '.txt':
        return TXTReader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# Convenience functions for backward compatibility
def render_pdf_content(file_path: str) -> ft.Container:
    return PDFReader(file_path).render()


def render_txt_content(file_path: str) -> ft.Container:
    return TXTReader(file_path).render()