"""
Image annotation library for creating visual feedback annotations.

Provides sketch-style annotations for photo scoring and feedback.
"""

import os
from typing import Union
from PIL import Image, ImageDraw, ImageFont
import numpy as np


class ImageAnnotator:
    """
    A library to annotate images with sketch-style lines, ellipses, text,
    composition guides, scores, and teacher comments, mimicking a hand-marked style.
    """

    def __init__(self, image_source: Union[str, Image.Image]):
        """
        Initialize the annotator with an image.
        
        Args:
            image_source: Either a file path or PIL Image object
        """
        if isinstance(image_source, str):
            self.base_image = Image.open(image_source).convert("RGBA")
        else:
            self.base_image = image_source.convert("RGBA")

        self.width, self.height = self.base_image.size
        
        # Load font from local font directory
        font_path = os.path.join(os.path.dirname(__file__), 'font', 'GochiHand-Regular.ttf')
        self.font_available = os.path.exists(font_path)
        self.font_path = font_path if self.font_available else None
        
        # Initialize overlay layers
        self.annotation_overlay = Image.new("RGBA", self.base_image.size, (255, 255, 255, 0))
        self.draw_annotations = ImageDraw.Draw(self.annotation_overlay)

        self.top_overlay = Image.new("RGBA", self.base_image.size, (255, 255, 255, 0))
        self.draw_top = ImageDraw.Draw(self.top_overlay)

        # Initialize drawing parameters
        self._setup_drawing_parameters()

    def _setup_drawing_parameters(self):
        """Configure drawing colors and parameters."""
        # Colors with improved opacity
        self.vermillion_opaque = (227, 66, 52, 255)
        self.vermillion_semi_transparent = (227, 66, 52, int(255 * 0.70))

        # Font sizes optimized for visibility - reduced for better proportion
        self.annotation_font_size = 36
        self.note_font_size = 24
        
        # Drawing parameters for sketch effect
        self.line_jitter = 5
        self.line_count = 5
        self.line_width = 6
        self.ellipse_jitter = 5
        self.ellipse_count = 4
        self.ellipse_width = 6

    def get_font(self, size: int) -> ImageFont.ImageFont:
        """
        Load font with fallback to default.
        
        Args:
            size: Font size
            
        Returns:
            ImageFont: Font object
        """
        if self.font_available and self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except Exception:
                pass
        
        # Fallback to default font
        return ImageFont.load_default()

    def draw_sketch_line(self, start_point: tuple, end_point: tuple):
        """
        Draw a hand-sketched style line between two points.
        
        Args:
            start_point: (x, y) start coordinates
            end_point: (x, y) end coordinates
        """
        for _ in range(self.line_count):
            s_jittered = (
                start_point[0] + np.random.randint(-self.line_jitter, self.line_jitter + 1),
                start_point[1] + np.random.randint(-self.line_jitter, self.line_jitter + 1)
            )
            e_jittered = (
                end_point[0] + np.random.randint(-self.line_jitter, self.line_jitter + 1),
                end_point[1] + np.random.randint(-self.line_jitter, self.line_jitter + 1)
            )
            self.draw_annotations.line(
                [s_jittered, e_jittered], 
                fill=self.vermillion_semi_transparent, 
                width=self.line_width
            )

    def draw_open_ellipse(self, center: tuple, radius_x: int, radius_y: int, on_top: bool = False):
        """
        Draw an open elliptical arc with sketch effect.
        
        Args:
            center: (x, y) center coordinates
            radius_x: X-axis radius
            radius_y: Y-axis radius
            on_top: Whether to draw on top overlay
        """
        draw_context = self.draw_top if on_top else self.draw_annotations
        cx, cy = center

        for _ in range(self.ellipse_count):
            start_angle = np.random.uniform(10, 330)
            end_angle = start_angle + np.random.uniform(180, 300)
            bbox = [
                cx - radius_x + np.random.randint(-self.ellipse_jitter, self.ellipse_jitter + 1),
                cy - radius_y + np.random.randint(-self.ellipse_jitter, self.ellipse_jitter + 1),
                cx + radius_x + np.random.randint(-self.ellipse_jitter, self.ellipse_jitter + 1),
                cy + radius_y + np.random.randint(-self.ellipse_jitter, self.ellipse_jitter + 1),
            ]
            draw_context.arc(
                bbox, 
                start=start_angle, 
                end=end_angle, 
                fill=self.vermillion_semi_transparent, 
                width=self.ellipse_width
            )

    def add_rule_of_thirds_grid(self):
        """Add rule of thirds composition grid."""
        inset_x = int(self.width * 0.04)
        inset_y = int(self.height * 0.04)

        third_x_points = [self.width // 3, 2 * self.width // 3]
        third_y_points = [self.height // 3, 2 * self.height // 3]

        # Draw vertical lines
        for x_val in third_x_points:
            self.draw_sketch_line((x_val, inset_y), (x_val, self.height - inset_y))
        
        # Draw horizontal lines
        for y_val in third_y_points:
            self.draw_sketch_line((inset_x, y_val), (self.width - inset_x, y_val))

    def add_annotation_point(self, number_text: str, text_position: tuple, circle_center: tuple):
        """
        Add a numbered annotation point with circle.
        
        Args:
            number_text: Text to display (e.g., "1", "A")
            text_position: (x, y) position for text
            circle_center: (x, y) center for circle
        """
        font = self.get_font(self.annotation_font_size)
        
        # Draw circle around the center
        self.draw_open_ellipse(circle_center, 25, 25, on_top=False)
        
        # Center the text within the circle
        text_width = self._get_text_width(str(number_text), font)
        text_height = self.annotation_font_size
        
        # Calculate centered position
        centered_x = circle_center[0] - text_width // 2
        centered_y = circle_center[1] - text_height // 2
        
        # Add text with full opacity at centered position
        self.draw_annotations.text((centered_x, centered_y), str(number_text), font=font, fill=self.vermillion_opaque)

    def add_score(self, score_text: str, text_position: tuple, circle_center: tuple):
        """
        Add score with circle in top area.
        
        Args:
            score_text: Score to display (e.g., "82")
            text_position: (x, y) position for text (ignored, auto-centered)
            circle_center: (x, y) center for circle
        """
        font = self.get_font(self.annotation_font_size)
        
        # Draw circle around score
        self.draw_open_ellipse(circle_center, 35, 35, on_top=True)
        
        # Center the score text within the circle
        text_width = self._get_text_width(str(score_text), font)
        text_height = self.annotation_font_size
        
        # Calculate centered position
        centered_x = circle_center[0] - text_width // 2
        centered_y = circle_center[1] - text_height // 2
        
        # Add score text at centered position
        self.draw_top.text((centered_x, centered_y), str(score_text), font=font, fill=self.vermillion_opaque)

    def add_score_divider(self, y_position: int, start_x: int, end_x: int):
        """
        Add horizontal divider line below score.
        
        Args:
            y_position: Y coordinate for the line
            start_x: Starting X coordinate
            end_x: Ending X coordinate
        """
        for _ in range(self.line_count):
            s_jittered = (
                start_x + np.random.randint(-self.line_jitter, self.line_jitter + 1),
                y_position + np.random.randint(-self.line_jitter, self.line_jitter + 1)
            )
            e_jittered = (
                end_x + np.random.randint(-self.line_jitter, self.line_jitter + 1),
                y_position + np.random.randint(-self.line_jitter, self.line_jitter + 1)
            )
            self.draw_top.line(
                [s_jittered, e_jittered], 
                fill=self.vermillion_semi_transparent, 
                width=self.line_width
            )

    def add_teacher_comment(self, comment_text: str):
        """
        Add teacher comment in top-right area with automatic positioning and word wrap.
        
        Args:
            comment_text: The comment text to add
        """
        font = self.get_font(self.note_font_size)
        
        # Calculate positioning
        start_y = 140
        max_width = int(self.width * 0.35)
        right_margin = 20
        line_height = 30

        # Word wrap the text
        wrapped_lines = self._wrap_text(comment_text, font, max_width)

        # Shadow color (50% white)
        shadow_color = (255, 255, 255, 128)

        # Draw each line with shadow effect
        current_y = start_y
        for line_text in wrapped_lines:
            text_width = self._get_text_width(line_text, font)
            x_text = self.width - right_margin - text_width
            
            # First draw shadow with 50% white
            self.draw_top.text((x_text, current_y), line_text, font=font, fill=shadow_color)
            
            # Then draw main text 1px down and 1px right
            self.draw_top.text((x_text + 1, current_y + 1), line_text, font=font, fill=self.vermillion_opaque)
            
            current_y += line_height

    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> list:
        """Wrap text to fit within specified width."""
        words = text.split()
        wrapped_lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip()
            text_width = self._get_text_width(test_line, font)
                
            if text_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped_lines.append(current_line)
                current_line = word
        
        if current_line:
            wrapped_lines.append(current_line)
            
        return wrapped_lines

    def _get_text_width(self, text: str, font: ImageFont.ImageFont) -> int:
        """Get text width with fallback for older PIL versions."""
        try:
            return font.getlength(text)
        except AttributeError:
            # Fallback for older PIL versions
            return len(text) * 25

    def save_image(self, output_path: str = 'annotated_output.jpg') -> Image.Image:
        """
        Save the annotated image and return the final image.
        
        Args:
            output_path: Path to save the image
            
        Returns:
            Image: The final annotated image
        """
        # Composite all layers
        composited_image = Image.alpha_composite(self.base_image, self.annotation_overlay)
        final_image = Image.alpha_composite(composited_image, self.top_overlay)
        
        # Convert to RGB and save
        final_rgb = final_image.convert("RGB")
        final_rgb.save(output_path)
        
        return final_rgb 