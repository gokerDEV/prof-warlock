"""
QR Code service for Prof. Warlock.

Generates SVG QR codes that can be placed in templates.
"""

import qrcode
from qrcode.image.svg import SvgPathImage
from typing import Optional
import os
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

class QRCodeService:
    """Service for generating QR codes in SVG format."""
    
    @staticmethod
    def generate_qr_code(url: str, size: int = 200, border: int = 4, 
                        fill_color: str = "#000000", background_color: str = "#ffffff") -> str:
        """
        Generate a QR code as SVG string.
        
        Args:
            url: The URL to encode in the QR code
            size: The size of the QR code in pixels
            border: The border size in modules (default: 4)
            fill_color: The color of the QR code modules (default: black)
            background_color: The background color (default: white)
            
        Returns:
            str: SVG string containing the QR code
        """
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=border
            )
            
            # Add data
            qr.add_data(url)
            qr.make(fit=True)
            
            # Create SVG image
            img = qr.make_image(
                image_factory=SvgPathImage,
                fill_color=fill_color,
                back_color=background_color
            )
            
            # Get SVG string
            svg_str = img.to_string()
            
            # Ensure we have a proper SVG string
            if not isinstance(svg_str, str):
                svg_str = svg_str.decode('utf-8')
            
            # Add XML declaration if not present
            xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
            if not svg_str.lstrip().startswith('<?xml'):
                svg_str = xml_declaration + svg_str
            
            # Remove existing width and height attributes if present
            svg_str = re.sub(r'width="[^"]*"', '', svg_str)
            svg_str = re.sub(r'height="[^"]*"', '', svg_str)
            
            # Add size attributes to the SVG
            svg_str = svg_str.replace('<svg', f'<svg width="{size}" height="{size}"')
            
            return svg_str
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            # Return a minimal valid SVG in case of error
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="{background_color}"/>
    <text x="50%" y="50%" text-anchor="middle" fill="{fill_color}">QR Error</text>
</svg>'''
    
    @staticmethod
    def save_qr_code(url: str, output_path: str, size: int = 200, border: int = 4,
                    fill_color: str = "#000000", background_color: str = "#ffffff") -> None:
        """
        Generate and save a QR code as SVG file.
        
        Args:
            url: The URL to encode in the QR code
            output_path: Path where to save the SVG file
            size: The size of the QR code in pixels
            border: The border size in modules (default: 4)
            fill_color: The color of the QR code modules (default: black)
            background_color: The background color (default: white)
        """
        svg_str = QRCodeService.generate_qr_code(
            url=url,
            size=size,
            border=border,
            fill_color=fill_color,
            background_color=background_color
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save SVG file
        with open(output_path, 'w') as f:
            f.write(svg_str) 