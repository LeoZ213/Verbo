"""Gemini AI integration for image analysis."""

import base64
import io
import os
import requests
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class GeminiAnalyzer:
    """Handles all Gemini API interactions for image analysis."""

    def __init__(self, api_key: str = None):
        """
        Initialize Gemini analyzer.

        Args:
            api_key: Your Gemini API key. If None, loads from environment variable.
        """
        # Priority: passed key > environment variable > None
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model = "gemini-2.5-flash"

    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.api_key != ""

    def encode_image(self, image: Image.Image) -> str:
        """
        Encode PIL Image to base64.

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded string
        """
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def crop_region(self, image_path: str, x: float, y: float,
                   width: float, height: float) -> Image.Image:
        """
        Crop a region from an image.

        Args:
            image_path: Path to source image
            x, y: Top-left corner (0-1 normalized)
            width, height: Dimensions (0-1 normalized)

        Returns:
            Cropped PIL Image
        """
        img = Image.open(image_path)
        img_width, img_height = img.size

        left = int(x * img_width)
        top = int(y * img_height)
        right = int((x + width) * img_width)
        bottom = int((y + height) * img_height)

        return img.crop((left, top, right, bottom))

    def analyze_image(self, image: Image.Image, prompt: str) -> dict:
        """
        Send image to Gemini for analysis.

        Args:
            image: PIL Image to analyze
            prompt: Question or instruction for Gemini

        Returns:
            Dictionary with 'success', 'text', and 'error' keys
        """
        if not self.is_configured():
            return {
                'success': False,
                'text': '',
                'error': 'API key not configured. Add GEMINI_API_KEY to your .env file'
            }

        try:
            # Encode image
            image_data = self.encode_image(image)

            enhanced_prompt = f"{prompt}\n\nImportant: Provide your response in plain text only, without any markdown formatting, bold, italics, or special characters for emphasis."

            # Prepare request
            url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": enhanced_prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }]
            }

            # Make request
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return {
                    'success': True,
                    'text': text,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': '',
                    'error': 'No response from Gemini'
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'text': '',
                'error': 'Request timed out. Please try again.'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'text': '',
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'text': '',
                'error': f'Error: {str(e)}'
            }

    def capture_and_analyze(self, image_path: str, x: float, y: float,
                          width: float, height: float, prompt: str) -> tuple[Image.Image, dict]:
        """
        Crop region and analyze in one step.

        Args:
            image_path: Path to source image
            x, y: Top-left corner (0-1 normalized)
            width, height: Dimensions (0-1 normalized)
            prompt: Question for Gemini

        Returns:
            Tuple of (cropped_image, analysis_result_dict)
        """
        try:
            cropped = self.crop_region(image_path, x, y, width, height)
            result = self.analyze_image(cropped, prompt)
            return cropped, result
        except Exception as e:
            return None, {
                'success': False,
                'text': '',
                'error': f'Crop failed: {str(e)}'
            }


# Preset prompts for quick actions
class PromptPresets:
    """Common prompts for different analysis tasks."""

    EXTRACT_TEXT = "Extract all text from this image. Return only the text content, nothing else."
    SUMMARIZE = "Provide a concise summary of the content in this image."
    EXPLAIN = "Explain the content in this image clearly and concisely."
    TRANSLATE = "Translate all text in this image to English."
    FORMULAS = "List and explain all mathematical formulas shown in this image."
    KEY_POINTS = "Extract the key points from this content as a bullet list."