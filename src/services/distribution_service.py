"""
Distribution service for Prof. Warlock.

Handles the rendering of modality, polarity and hemisphere distributions using SVG paths.
"""

import logging
from PIL import ImageDraw, Image
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
    TEXT_COLOR = "#000000"
    
    # Symbol settings
    SYMBOL_SIZE = 40
    SYMBOL_SPACING = 5
    
    @staticmethod
    def _draw_category_line(draw: ImageDraw, bodies: List[str], x: int, y: int, width: int, height: int, svg_paths_dir: str) -> int:
        """Draw symbols in a line, centered in the given area. Returns the y position for the next line."""
        # Load SVG files
        SVGPathService._load_svg_files(svg_paths_dir)
        
        # Calculate total width of all symbols
        total_symbols_width = 0
        symbol_images = []
        for body in bodies:
            if body not in DistributionUtils.BODY_TO_SYMBOL:
                continue
                
            symbol = DistributionUtils.BODY_TO_SYMBOL[body]
            if sym_img := DistributionUtils.draw_symbol(symbol, size=DistributionService.SYMBOL_SIZE, color=DistributionService.TEXT_COLOR):
                symbol_images.append(sym_img)
                total_symbols_width += sym_img.width + DistributionService.SYMBOL_SPACING
        
        if not symbol_images:
            return y + height
        
        # Remove extra spacing from the end
        total_symbols_width -= DistributionService.SYMBOL_SPACING
        
        # Calculate starting x position to center the symbols
        start_x = x + (width - total_symbols_width) // 2
        
        # Draw symbols
        current_x = start_x
        for sym_img in symbol_images:
            paste_x = int(current_x)
            paste_y = int(y + (height - sym_img.height) // 2)  # Center vertically
            draw._image.paste(sym_img, (paste_x, paste_y), sym_img)
            current_x += sym_img.width + DistributionService.SYMBOL_SPACING
        
        return y + height  # Return position for next line

    @staticmethod
    def draw_modality_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], svg_paths_dir: str) -> None:
        """Draw modality distribution without labels."""
        if 'cardinal' not in rects or 'fixed' not in rects or 'mutable' not in rects:
            return
            
        # Get modality distribution
        distribution = stats.distribution('modality')
        modality_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw each modality line
        for modality in DistributionService.MODALITIES:
            if modality not in rects:
                continue
                
            rect = rects[modality]
            x = int(rect['center_x'] - rect['width'] / 2)
            y = int(rect['center_y'] - rect['height'] / 2)
            
            # Get bodies for this modality, or empty list if none
            bodies = modality_bodies.get(modality, [])
            
            DistributionService._draw_category_line(
                draw=draw,
                bodies=bodies,
                x=x,
                y=y,
                width=rect['width'],
                height=rect['height'],
                svg_paths_dir=svg_paths_dir
            )

    @staticmethod
    def draw_polarity_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], svg_paths_dir: str) -> None:
        """Draw polarity distribution without labels."""
        if 'positive' not in rects or 'negative' not in rects:
            return
            
        # Get polarity distribution
        distribution = stats.distribution('polarity')
        polarity_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw each polarity line
        for polarity in DistributionService.POLARITIES:
            if polarity not in rects:
                continue
                
            rect = rects[polarity]
            x = int(rect['center_x'] - rect['width'] / 2)
            y = int(rect['center_y'] - rect['height'] / 2)
            
            # Get bodies for this polarity, or empty list if none
            bodies = polarity_bodies.get(polarity, [])
            
            DistributionService._draw_category_line(
                draw=draw,
                bodies=bodies,
                x=x,
                y=y,
                width=rect['width'],
                height=rect['height'],
                svg_paths_dir=svg_paths_dir
            )

    @staticmethod
    def draw_hemisphere_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], svg_paths_dir: str) -> None:
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
        current_y = y
        for hemisphere in DistributionService.HEMISPHERES:
            # Get bodies for this hemisphere, or empty list if none
            bodies = hemisphere_bodies.get(hemisphere, [])
            
            current_y = DistributionService._draw_category_line(
                draw=draw,
                bodies=bodies,
                x=x,
                y=current_y,
                width=rect['width'],
                height=rect['height'] // 4,  # Divide height by 4 for each hemisphere
                svg_paths_dir=svg_paths_dir
            ) 