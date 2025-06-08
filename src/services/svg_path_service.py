"""
SVG Path Service for Prof. Warlock.

Common service for handling SVG paths and rendering symbols.
Used by both ElementDistributionService and AspectMatrixService.
"""

import os
import logging
from pathlib import Path
from PIL import Image
from io import BytesIO
import cairosvg
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SVGPathService:
    # Common settings
    CELL_SIZE = 75  # Fixed cell size
    BORDER_COLOR = (0, 0, 0, 255)  # Black color for borders
    BORDER_WIDTH = 2  # Border width for visibility

    # Mapping for all symbols to file names
    SYMBOL_MAP = {
        # Planet symbols
        '☉': 'sun', '☽': 'moon', '☿': 'mercury', '♀': 'venus', '♂': 'mars',
        '♃': 'jupiter', '♄': 'saturn', '♅': 'uranus', '♆': 'neptune', '♇': 'pluto',
        '☊': 'asc_node', 'Asc': 'asc', 'MC': 'mc',
        # Aspect symbols
        '☌': 'conjunction', '□': 'square', '△': 'trine', '⚹': 'sextile',
        '⚺': 'quincunx', '☍': 'opposition', '⚻': 'semisextile',
        '⚼': 'sesquiquadrate', '∠': 'semisquare',
    }

    _svg_cache: Dict[str, str] = {}

    @classmethod
    def _load_svg_files(cls, svg_paths_dir: str) -> None:
        """Load all SVG files into memory once."""
        if not cls._svg_cache:
            for symbol, filename in cls.SYMBOL_MAP.items():
                path = os.path.join(svg_paths_dir, f"{filename}.svg")
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        cls._svg_cache[filename] = f.read()
                else:
                    logger.warning(f"SVG file not found: {path}")

    @classmethod
    def _get_symbol_filename(cls, symbol: str) -> str:
        """Convert any symbol to its corresponding file name."""
        return cls.SYMBOL_MAP.get(symbol.strip(), '')

    @classmethod
    def render_symbol(cls, filename: str, size: int, color: str = 'black') -> Optional[Image.Image]:
        """Renders the SVG from the given filename into a PNG image of the desired size."""
        if filename in cls._svg_cache:
            path_content = cls._svg_cache[filename]
            
            fill_color = color if filename == 'asc'  or filename == 'mc' else 'none'
            stroke_width = '0' if filename == 'asc'  or filename == 'mc' else '1.5'
            
            # Create a complete SVG structure with larger viewBox
            svg_template = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 50 50">
    <g transform="translate(2,2) scale(2,2)" stroke="{color}" stroke-width="{stroke_width}" fill="{fill_color}">
        {path_content}
    </g>
</svg>'''
            
            try:
                png_data = cairosvg.svg2png(bytestring=svg_template.encode('utf-8'), 
                                          output_width=size, 
                                          output_height=size)
                return Image.open(BytesIO(png_data)).convert('RGBA')
            except Exception as e:
                logger.error(f"SVG -> PNG conversion error for {filename}: {e}")
                logger.error(f"SVG content: {svg_template}")
        return None 