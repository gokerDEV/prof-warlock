"""
Distribution service for Prof. Warlock.

Handles the rendering of modality, polarity and hemisphere distributions using SVG paths.
"""

import logging
from PIL import ImageDraw, Image, ImageFont
from typing import Dict, List
from natal.stats import Stats
from .distribution_utils import DistributionUtils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DistributionService:
    """Service for handling modality, polarity and hemisphere distribution visualization."""
    
    # Distribution categories
    MODALITIES = ['cardinal', 'fixed', 'mutable']
    POLARITIES = ['positive', 'negative']
    HEMISPHERES = ['←', '→', '↑', '↓']
    
    # Colors
    BACKGROUND_COLOR = "#393939"  
    TEXT_COLOR = "#fcf2de"  

    @staticmethod
    def _draw_category_label(draw: ImageDraw, text: str, rect: Dict, font: ImageFont) -> None:
        """Draw category label with background."""
        # Create a temporary canvas for the label
        label_width = rect['width']
        label_height = 40  # Fixed height for labels
        
        label_canvas = DistributionUtils.create_grid_canvas(label_width, label_height, DistributionService.BACKGROUND_COLOR)
        label_draw = ImageDraw.Draw(label_canvas)
        
        # Calculate text position to center it
        bbox = label_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (label_width - text_width) / 2
        y = (label_height - text_height) / 2
        
        # Draw text in TEXT_COLOR
        label_draw.text((x, y), text, font=font, fill=DistributionService.TEXT_COLOR)
        
        # Calculate position above the rect
        paste_x = int(rect['center_x'] - label_width / 2)
        paste_y = int(rect['center_y'] - rect['height'] / 2 - label_height - 10)  # 10px gap
        
        # Paste the label onto the main canvas
        draw._image.paste(label_canvas, (paste_x, paste_y), label_canvas)

    @staticmethod
    def _draw_symbol_grid(draw: ImageDraw, bodies: List[str], rect: Dict) -> None:
        """Draw symbols in a grid with background."""
        # Create a temporary canvas for this category's grid
        grid_width = rect['width']
        grid_height = rect['height']
        
        # Create canvas and calculate positions
        grid_canvas = DistributionUtils.create_grid_canvas(grid_width, grid_height, DistributionService.BACKGROUND_COLOR)
        positions = DistributionUtils.calculate_grid_positions(grid_width, grid_height)
        
        # Draw each body's symbol in the grid
        for i, body in enumerate(bodies[:9]):  # Limit to 9 symbols (3x3 grid)
            if body not in DistributionUtils.BODY_TO_SYMBOL:
                continue
                
            symbol = DistributionUtils.BODY_TO_SYMBOL[body]
            x, y, cell_width, _ = positions[i]
            
            if sym_img := DistributionUtils.draw_symbol(symbol, size=int(cell_width * 0.8), color=DistributionService.TEXT_COLOR):
                DistributionUtils.paste_centered(grid_canvas, sym_img, x, y)
        
        # Calculate paste position to center the grid
        paste_x = int(rect['center_x'] - grid_width / 2)
        paste_y = int(rect['center_y'] - grid_height / 2)
        
        # Paste the grid onto the main canvas
        draw._image.paste(grid_canvas, (paste_x, paste_y), grid_canvas)

    @staticmethod
    def draw_modality_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont) -> None:
        """Draw modality distribution with labels."""
        # Get modality distribution from stats
        distribution = stats.distribution('modality')
        modality_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw symbols and labels for each modality
        for modality in DistributionService.MODALITIES:
            if modality not in rects or modality not in modality_bodies:
                continue
                
            # Draw label
            DistributionService._draw_category_label(draw, modality.title(), rects[modality], font)
            
            # Draw symbol grid
            DistributionService._draw_symbol_grid(
                draw=draw,
                bodies=modality_bodies[modality],
                rect=rects[modality]
            )

    @staticmethod
    def draw_polarity_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont) -> None:
        """Draw polarity distribution with labels."""
        # Get polarity distribution from stats
        distribution = stats.distribution('polarity')
        polarity_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw symbols and labels for each polarity
        for polarity in DistributionService.POLARITIES:
            if polarity not in rects or polarity not in polarity_bodies:
                continue
                
            # Draw label
            DistributionService._draw_category_label(draw, polarity.title(), rects[polarity], font)
            
            # Draw symbol grid
            DistributionService._draw_symbol_grid(
                draw=draw,
                bodies=polarity_bodies[polarity],
                rect=rects[polarity]
            )

    @staticmethod
    def draw_hemisphere_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], font: ImageFont) -> None:
        """Draw hemisphere distribution with labels."""
        # Get hemisphere distribution from stats
        distribution = stats.hemispheres
        hemisphere_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid, skip_header=False)
        
        # Draw symbols and labels for each hemisphere
        for hemisphere in DistributionService.HEMISPHERES:
            if hemisphere not in rects or hemisphere not in hemisphere_bodies:
                continue
                
            # Draw label
            label_text = {
                '←': 'Left',
                '→': 'Right',
                '↑': 'Above',
                '↓': 'Below'
            }.get(hemisphere, hemisphere)
            
            DistributionService._draw_category_label(draw, label_text, rects[hemisphere], font)
            
            # Draw symbol grid
            DistributionService._draw_symbol_grid(
                draw=draw,
                bodies=hemisphere_bodies[hemisphere],
                rect=rects[hemisphere]
            ) 