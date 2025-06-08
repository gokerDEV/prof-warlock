"""
Distribution service for Prof. Warlock.

Handles the rendering of modality, polarity and hemisphere distributions using SVG paths.
"""

import logging
from PIL import ImageDraw, Image, ImageFont
from typing import Dict, List
from natal.stats import Stats
from .distribution_utils import DistributionUtils
from .svg_path_service import SVGPathService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DistributionService:
    """Service for handling modality, polarity and hemisphere distribution visualization."""
    
    # Distribution categories
    MODALITIES = ['cardinal', 'fixed', 'mutable']
    POLARITIES = ['positive', 'negative']
    HEMISPHERES = ['←', '→', '↑', '↓']
    
    # Colors
    TEXT_COLOR = "#fcf2de"  # Light beige text

    @staticmethod
    def _draw_category_line(draw: ImageDraw, label: str, bodies: List[str], x: int, y: int, font: ImageFont, svg_paths_dir: str) -> int:
        """Draw a category label followed by its symbols in a line. Returns the y position for the next line."""
        # Draw label
        draw.text((x, y), f"{label}: ", font=font, fill=DistributionService.TEXT_COLOR)
        
        # Calculate width of label to know where to start symbols
        bbox = draw.textbbox((x, y), f"{label}: ", font=font)
        symbol_x = bbox[2] + 10  # Add some spacing after label
        symbol_size = font.size * 1.1 # Use font size for symbols
        symbol_spacing = symbol_size + 5  # Add some spacing between symbols
        
        # Load SVG files
        SVGPathService._load_svg_files(svg_paths_dir)
        
        # Draw symbols
        for body in bodies:
            if body not in DistributionUtils.BODY_TO_SYMBOL:
                continue
                
            symbol = DistributionUtils.BODY_TO_SYMBOL[body]
            if sym_img := DistributionUtils.draw_symbol(symbol, size=symbol_size, color=DistributionService.TEXT_COLOR):
                paste_x = int(symbol_x)
                paste_y = int(y + (font.size - sym_img.height) / 2) + 8  # Center vertically with text
                draw._image.paste(sym_img, (paste_x, paste_y), sym_img)
                symbol_x += symbol_spacing
        
        return y + font.size + 10  # Return position for next line with some spacing

    @staticmethod
    def draw_modality_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont, svg_paths_dir: str) -> None:
        """Draw modality distribution with labels."""
        if 'modality' not in rects:
            return
            
        rect = rects['modality']
        x = int(rect['center_x'] - rect['width'] / 2)
        y = int(rect['center_y'] - rect['height'] / 2)
        
        # Get modality distribution
        distribution = stats.distribution('modality')
        modality_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw each modality line
        current_y = y + 10  # Start with some margin
        for modality in DistributionService.MODALITIES:
            # Get bodies for this modality, or empty list if none
            bodies = modality_bodies.get(modality, [])
            
            current_y = DistributionService._draw_category_line(
                draw=draw,
                label=modality.title(),
                bodies=bodies,
                x=x + 10,
                y=current_y,
                font=font,
                svg_paths_dir=svg_paths_dir
            )

    @staticmethod
    def draw_polarity_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont, svg_paths_dir: str) -> None:
        """Draw polarity distribution with labels."""
        if 'polarity' not in rects:
            return
            
        rect = rects['polarity']
        x = int(rect['center_x'] - rect['width'] / 2)
        y = int(rect['center_y'] - rect['height'] / 2)
        
        # Get polarity distribution
        distribution = stats.distribution('polarity')
        polarity_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw each polarity line
        current_y = y + 10  # Start with some margin
        for polarity in DistributionService.POLARITIES:
            # Get bodies for this polarity, or empty list if none
            bodies = polarity_bodies.get(polarity, [])
            
            current_y = DistributionService._draw_category_line(
                draw=draw,
                label=polarity.title(),
                bodies=bodies,
                x=x + 10,
                y=current_y,
                font=font,
                svg_paths_dir=svg_paths_dir
            )

    @staticmethod
    def draw_hemisphere_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont, svg_paths_dir: str) -> None:
        """Draw hemisphere distribution with labels."""
        if 'hemisphere' not in rects:
            return
            
        rect = rects['hemisphere']
        x = int(rect['center_x'] - rect['width'] / 2)
        y = int(rect['center_y'] - rect['height'] / 2)
        
        # Get hemisphere distribution
        distribution = stats.hemisphere
        hemisphere_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid, skip_header=False)
        
        # Draw each hemisphere line
        current_y = y + 10  # Start with some margin
        for hemisphere in DistributionService.HEMISPHERES:
            # Get bodies for this hemisphere, or empty list if none
            bodies = hemisphere_bodies.get(hemisphere, [])
            
            label_text = {
                '←': 'Left',
                '→': 'Right',
                '↑': 'Above',
                '↓': 'Below'
            }.get(hemisphere, hemisphere)
            
            current_y = DistributionService._draw_category_line(
                draw=draw,
                label=label_text,
                bodies=bodies,
                x=x + 10,
                y=current_y,
                font=font,
                svg_paths_dir=svg_paths_dir
            ) 