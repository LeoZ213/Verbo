import flet as ft
import fitz
import tempfile
import os
from abc import ABC, abstractmethod
from pathlib import Path
from PIL import Image
import threading

# Import AI functionality
from src.utils.gemini_integration import GeminiAnalyzer, PromptPresets


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
    """PDF book reader with AI analysis"""

    def __init__(self, file_path: str, api_key: str = None):
        super().__init__(file_path)
        self.document = None
        self.temp_dir = None
        self.zoom_level = 1.0
        self.capture_mode = False
        self.panel_width = 400
        # Initialize AI analyzer
        self.ai_analyzer = GeminiAnalyzer(api_key)

    def load(self):
        """Load the PDF document"""
        self.document = fitz.open(self.file_path)
        self.temp_dir = tempfile.mkdtemp()

    def get_content(self, position: int):
        """Render a PDF page to an image"""
        if not self.document:
            return None

        page = self.document[position]
        mat = fitz.Matrix(self.zoom_level, self.zoom_level)
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(self.temp_dir, f"page_{position}_zoom_{self.zoom_level}.png")
        pix.save(img_path)
        return os.path.abspath(img_path)

    def get_total_items(self) -> int:
        return len(self.document) if self.document else 0

    def render(self) -> ft.Container:
        """Render PDF reader UI with AI analysis panel"""
        self.load()

        # UI Components
        page_image = ft.Image(fit=ft.ImageFit.NONE, key="img_0")
        page_info = ft.Text(f"Page 1 of {self.get_total_items()}", color=ft.Colors.ON_INVERSE_SURFACE)
        zoom_info = ft.Text(f"Zoom: {int(self.zoom_level * 100)}%", color=ft.Colors.ON_INVERSE_SURFACE)

        # Capture mode indicator
        capture_indicator = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.CROP, color=ft.Colors.AMBER),
                ft.Text("Capture Mode: Draw a box and it will be sent to Gemini", color=ft.Colors.AMBER)
            ], spacing=5),
            visible=False,
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.BLACK),
        )

        # Selection overlay
        selection_start = [None, None]
        selection_rect = ft.Container(
            border=ft.border.all(3, ft.Colors.AMBER),
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.AMBER),
            visible=False,
        )

        img_counter = [0]
        current_image_path = [None]

        image_switcher = ft.AnimatedSwitcher(
            page_image,
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=150,
            reverse_duration=150,
            switch_in_curve=ft.AnimationCurve.EASE_IN,
            switch_out_curve=ft.AnimationCurve.EASE_OUT,
        )

        # Container to hold image
        image_container = ft.Container(
            content=image_switcher,
            expand=True,
        )

        # Stack for image and selection overlay
        image_stack = ft.Stack(
            [
                image_container,
                selection_rect,
            ],
            expand=True,
        )

        # Right panel for AI analysis
        panel_visible = [True]

        prompt_field = ft.TextField(
            label="What do you want to know?",
            hint_text="e.g., 'Explain this', 'Summarize', 'Extract text'",
            value=PromptPresets.EXPLAIN,
            multiline=True,
            min_lines=2,
            max_lines=3,
            text_size=12,
        )

        captured_preview = ft.Image(
            fit=ft.ImageFit.CONTAIN,
            width=300,
            visible=False,
        )

        analysis_text = ft.TextField(
            label="Gemini Analysis",
            multiline=True,
            read_only=True,
            min_lines=15,
            expand=True,
            text_size=13,
        )

        loading_indicator = ft.ProgressRing(visible=False, width=20, height=20)
        status_text = ft.Text("", size=11, color=ft.Colors.GREY_700)

        # Quick action buttons using presets
        def set_extract_text(e):
            prompt_field.value = PromptPresets.EXTRACT_TEXT
            prompt_field.update()

        def set_summarize(e):
            prompt_field.value = PromptPresets.SUMMARIZE
            prompt_field.update()

        def set_explain(e):
            prompt_field.value = PromptPresets.EXPLAIN
            prompt_field.update()

        quick_actions = ft.Row([
            ft.OutlinedButton("Extract Text", on_click=set_extract_text, icon=ft.Icons.TEXT_FIELDS,
                              style=ft.ButtonStyle(padding=5)),
            ft.OutlinedButton("Summarize", on_click=set_summarize, icon=ft.Icons.SUMMARIZE,
                              style=ft.ButtonStyle(padding=5)),
            ft.OutlinedButton("Explain", on_click=set_explain, icon=ft.Icons.LIGHTBULB,
                              style=ft.ButtonStyle(padding=5)),
        ], spacing=5, wrap=True)

        def toggle_panel(e):
            panel_visible[0] = not panel_visible[0]
            right_panel.visible = panel_visible[0]
            if panel_visible[0]:
                toggle_panel_button.icon = ft.Icons.CLOSE_FULLSCREEN
                toggle_panel_button.tooltip = "Close AI Panel"
            else:
                toggle_panel_button.icon = ft.Icons.OPEN_IN_FULL
                toggle_panel_button.tooltip = "Open AI Panel"
            toggle_panel_button.update()
            right_panel.update()

        toggle_panel_button = ft.IconButton(
            icon=ft.Icons.CLOSE_FULLSCREEN,
            tooltip="Close AI Panel",
            on_click=toggle_panel,
        )

        # Resizable divider
        resize_handle = ft.GestureDetector(
            content=ft.Container(
                width=8,
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                border=ft.border.only(left=ft.BorderSide(1, ft.Colors.GREY_400)),
            ),
            on_horizontal_drag_update=lambda e: resize_panel(e),
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

        def resize_panel(e: ft.DragUpdateEvent):
            new_width = self.panel_width - e.delta_x
            new_width = max(250, min(600, new_width))
            self.panel_width = new_width
            right_panel.width = new_width
            right_panel.update()

        right_panel = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("AI Analysis", size=16, weight=ft.FontWeight.BOLD),
                    toggle_panel_button,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1),
                prompt_field,
                quick_actions,
                ft.Divider(height=1),
                ft.Text("Captured Region:", size=12, weight=ft.FontWeight.BOLD),
                captured_preview,
                ft.Row([loading_indicator, status_text], spacing=10),
                analysis_text,
            ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
            width=self.panel_width,
            padding=15,
            bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
        )

        def update_page():
            img_path = self.get_content(self.current_position)
            current_image_path[0] = img_path

            if self.zoom_level <= 1.0:
                fit_mode = ft.ImageFit.CONTAIN
            else:
                fit_mode = ft.ImageFit.NONE

            img_counter[0] += 1
            new_image = ft.Image(
                src=img_path,
                fit=fit_mode,
                key=f"img_{img_counter[0]}"
            )

            page_info.value = f"Page {self.current_position + 1} of {self.get_total_items()}"
            zoom_info.value = f"Zoom: {int(self.zoom_level * 100)}%"

            image_switcher.content = new_image
            selection_rect.visible = False

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
            if self.zoom_level < 3.0:
                self.zoom_level += 0.25
                update_page()

        def zoom_out(e):
            if self.zoom_level > 0.5:
                self.zoom_level -= 0.25
                update_page()

        def reset_zoom(e):
            self.zoom_level = 1.0
            update_page()

        def toggle_capture_mode(e):
            self.capture_mode = not self.capture_mode
            capture_indicator.visible = self.capture_mode
            selection_rect.visible = False

            if self.capture_mode:
                capture_button.bgcolor = ft.Colors.AMBER
                capture_button.icon_color = ft.Colors.BLACK
            else:
                capture_button.bgcolor = None
                capture_button.icon_color = None

            capture_button.update()
            capture_indicator.update()

        def on_pan_start(e: ft.DragStartEvent):
            if not self.capture_mode:
                return

            selection_start[0] = e.local_x
            selection_start[1] = e.local_y

            selection_rect.left = e.local_x
            selection_rect.top = e.local_y
            selection_rect.width = 0
            selection_rect.height = 0
            selection_rect.visible = True
            selection_rect.update()

        def on_pan_update(e: ft.DragUpdateEvent):
            if not self.capture_mode or selection_start[0] is None:
                return

            current_x = e.local_x
            current_y = e.local_y

            width = abs(current_x - selection_start[0])
            height = abs(current_y - selection_start[1])

            left = min(selection_start[0], current_x)
            top = min(selection_start[1], current_y)

            selection_rect.left = left
            selection_rect.top = top
            selection_rect.width = width
            selection_rect.height = height
            selection_rect.update()

        def on_pan_end(e: ft.DragEndEvent):
            if not self.capture_mode or selection_start[0] is None:
                return

            if not current_image_path[0]:
                return

            if selection_rect.width < 10 or selection_rect.height < 10:
                selection_rect.visible = False
                selection_rect.update()
                selection_start[0] = None
                selection_start[1] = None
                return

            if not self.ai_analyzer.is_configured():
                status_text.value = "⚠ API key not configured. Set it in gemini_integration.py"
                status_text.color = ft.Colors.RED
                status_text.update()
                return

            try:
                img = Image.open(current_image_path[0])
                img_width, img_height = img.size

                x_norm = selection_rect.left / img_width
                y_norm = selection_rect.top / img_height
                width_norm = selection_rect.width / img_width
                height_norm = selection_rect.height / img_height

                # Show panel if hidden
                if not panel_visible[0]:
                    panel_visible[0] = True
                    right_panel.visible = True
                    toggle_panel_button.icon = ft.Icons.CLOSE_FULLSCREEN
                    toggle_panel_button.tooltip = "Close AI Panel"
                    toggle_panel_button.update()
                    right_panel.update()

                # Show loading
                loading_indicator.visible = True
                status_text.value = "Analyzing with Gemini..."
                status_text.color = ft.Colors.BLUE
                analysis_text.value = ""
                loading_indicator.update()
                status_text.update()

                # Make API call in background using the AI module
                def api_call():
                    try:
                        cropped_img, result = self.ai_analyzer.capture_and_analyze(
                            current_image_path[0],
                            x_norm,
                            y_norm,
                            width_norm,
                            height_norm,
                            prompt_field.value
                        )

                        if cropped_img:
                            # Save preview temporarily
                            preview_path = os.path.join(self.temp_dir, "preview.png")
                            cropped_img.save(preview_path)
                            captured_preview.src = preview_path
                            captured_preview.visible = True

                        if result['success']:
                            analysis_text.value = result['text']
                            status_text.value = "✓ Analysis complete"
                            status_text.color = ft.Colors.GREEN
                        else:
                            analysis_text.value = result['error']
                            status_text.value = "❌ Analysis failed"
                            status_text.color = ft.Colors.RED

                    except Exception as ex:
                        analysis_text.value = f"Error: {str(ex)}"
                        status_text.value = "❌ Error"
                        status_text.color = ft.Colors.RED

                    finally:
                        loading_indicator.visible = False
                        if loading_indicator.page:
                            loading_indicator.update()
                            captured_preview.update()
                            analysis_text.update()
                            status_text.update()

                threading.Thread(target=api_call, daemon=True).start()

                # Reset selection
                selection_rect.visible = False
                selection_rect.update()
                selection_start[0] = None
                selection_start[1] = None

            except Exception as ex:
                print(f"[ERROR] Capture failed: {ex}")

        # Initialize
        update_page()

        # Capture mode button
        capture_button = ft.IconButton(
            icon=ft.Icons.CROP,
            on_click=toggle_capture_mode,
            tooltip="Capture Mode - Select region to analyze with Gemini"
        )

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
                ft.VerticalDivider(),
                capture_button,
            ]),
            padding=10,
            bgcolor=ft.Colors.INVERSE_SURFACE,
        )

        # Scrollable container with gesture detection
        scrollable_content = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.GestureDetector(
                                content=image_stack,
                                on_pan_start=on_pan_start,
                                on_pan_update=on_pan_update,
                                on_pan_end=on_pan_end,
                            )
                        ],
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

        # Main layout with split view and resizable divider
        return ft.Row([
            ft.Container(
                content=ft.Column([
                    toolbar,
                    capture_indicator,
                    scrollable_content,
                ], spacing=10, expand=True),
                expand=True,
            ),
            resize_handle,
            right_panel,
        ], expand=True)


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
        return 1

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
        )

        zoom_info = ft.Text(f"Font: {self.font_size}px", color=ft.Colors.ON_INVERSE_SURFACE)

        def zoom_in(e):
            if self.font_size < 32:
                self.font_size += 2
                text_display.text_size = self.font_size
                zoom_info.value = f"Font: {self.font_size}px"
                text_display.update()
                zoom_info.update()

        def zoom_out(e):
            if self.font_size > 8:
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


# Factory function
def create_reader(file_path: str, api_key: str = None) -> BookReader:
    """Create appropriate reader based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return PDFReader(file_path, api_key)
    elif ext == '.txt':
        return TXTReader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


# Convenience functions
def render_pdf_content(file_path: str, api_key: str = None) -> ft.Container:
    return PDFReader(file_path, api_key).render()


def render_txt_content(file_path: str) -> ft.Container:
    return TXTReader(file_path).render()