"""
Image processing service.

Handles image preprocessing, scaling, and format standardization.
"""

import io
from typing import Tuple
from PIL import Image as PILImage
import logging

from ..core.domain_models import ProcessedImage, EmailAttachment


class ImageProcessingService:
    """Service for processing and standardizing images."""
    
    @staticmethod
    def process_image_attachment(attachment: EmailAttachment) -> ProcessedImage:
        """
        Process an image attachment into standardized format.
        
        Args:
            attachment: The image attachment to process
            
        Returns:
            ProcessedImage: Processed image with metadata and scaled content
        """
        processed_bytes, width, height = ImageProcessingService._preprocess_image_data(
            attachment.content
        )
        
        return ProcessedImage(
            image_path=attachment.name,
            width=width,
            height=height,
            original_filename=attachment.name,
            content_type=attachment.content_type,
            scaled_content=processed_bytes
        )
    
    @staticmethod
    def _preprocess_image_data(image_data: bytes) -> Tuple[bytes, int, int]:
        """
        Preprocess image according to standardized scaling rules:
        - Non-square: longest edge becomes 1200px
        - Square: scaled to 800x800px
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Tuple of (processed_image_bytes, width, height)
        """
        try:
            # Load image
            img = PILImage.open(io.BytesIO(image_data))
            original_width, original_height = img.size
            
            logging.info(f"Original image size: {original_width}x{original_height}")
            
            # Determine target size based on aspect ratio
            new_size = ImageProcessingService._calculate_target_size(
                original_width, original_height
            )
            
            # Resize image
            img_resized = img.resize(new_size, PILImage.Resampling.LANCZOS)
            
            logging.info(f"Scaled image size: {new_size[0]}x{new_size[1]}")
            
            # Convert to RGB and save as bytes
            if img_resized.mode != 'RGB':
                img_resized = img_resized.convert('RGB')
            
            output_buffer = io.BytesIO()
            img_resized.save(output_buffer, format='JPEG', quality=95)
            processed_bytes = output_buffer.getvalue()
            
            return processed_bytes, new_size[0], new_size[1]
            
        except Exception as e:
            logging.error(f"Image preprocessing failed: {e}", exc_info=True)
            # Return original if preprocessing fails
            return image_data, 800, 600  # Default fallback size
    
    @staticmethod
    def _calculate_target_size(width: int, height: int) -> Tuple[int, int]:
        """Calculate target size based on aspect ratio."""
        aspect_ratio = width / height
        is_square = 0.95 <= aspect_ratio <= 1.05  # Allow small tolerance for "square"
        
        if is_square:
            # Square images → 800x800
            return (800, 800)
        else:
            # Non-square: longest edge becomes 1200px
            if width > height:
                # Landscape
                new_width = 1200
                new_height = int((height / width) * 1200)
            else:
                # Portrait
                new_height = 1200
                new_width = int((width / height) * 1200)
            return (new_width, new_height) 