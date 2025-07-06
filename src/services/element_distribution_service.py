"""
Element distribution service for Prof. Warlock.

Handles the rendering of element distribution (earth, water, fire, air) using SVG paths.
"""

import logging
from PIL import ImageDraw, Image
from typing import Dict, List
from natal.stats import Stats
from .distribution_utils import DistributionUtils
from .svg_path_service import SVGPathService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElementDistributionService:
    """Service for handling element distribution visualization."""

    ELEMENTS = ['fire', 'earth', 'air', 'water']
    
    # Fixed rotation angles for each element
    ELEMENT_ROTATIONS = {
        'earth': -45,
        'air': -45,
        'water': 45,
        'fire': 45
    }

    # Colors
    SYMBOL_COLOR = "#393939"  # Same as DistributionService.BACKGROUND_COLOR

    @staticmethod
    def _draw_symbol_grid(draw: ImageDraw, bodies: List[str], rect: Dict, rotation: float) -> None:
        """Draw symbols in a grid with the specified rotation."""
        # Fixed dimensions and padding
        PADDING = 40
        BASE_SYMBOL_SIZE = 60
        LARGE_SYMBOL_SIZE = 72
        GRID_COLS = 4
        MAX_SYMBOLS = 16
        
        # Calculate number of rows needed
        num_bodies = min(len(bodies), MAX_SYMBOLS)
        num_rows = (num_bodies + GRID_COLS - 1) // GRID_COLS
        
        # Set symbol size based on number of rows
        symbol_size = LARGE_SYMBOL_SIZE if num_rows < 4 else BASE_SYMBOL_SIZE
        
        # Calculate grid dimensions
        row_height = symbol_size
        total_width = (GRID_COLS * symbol_size) + PADDING
        total_height = (num_rows * row_height) + PADDING
        
        # Create canvas with padding
        grid_canvas = DistributionUtils.create_grid_canvas(total_width, total_height)
        
        # Draw each body's symbol in the grid
        for i, body in enumerate(bodies[:MAX_SYMBOLS]):
            if body not in DistributionUtils.BODY_TO_SYMBOL:
                continue
                
            symbol = DistributionUtils.BODY_TO_SYMBOL[body]
            
            # Calculate position with padding
            row = i // GRID_COLS
            col = i % GRID_COLS
            x = PADDING + col * symbol_size
            y = PADDING + row * row_height
            
            if sym_img := DistributionUtils.draw_symbol(symbol, size=symbol_size, color=ElementDistributionService.SYMBOL_COLOR):
                DistributionUtils.paste_centered(grid_canvas, sym_img, x, y)
        
        # Rotate and center the grid
        rotated_grid = grid_canvas.rotate(rotation, expand=True, resample=Image.BICUBIC)
        paste_x = int(rect['center_x'] - rotated_grid.width / 2)
        paste_y = int(rect['center_y'] - rotated_grid.height / 2)
        draw._image.paste(rotated_grid, (paste_x, paste_y), rotated_grid)

    @staticmethod
    def draw_element_distribution(draw: ImageDraw, stats: Stats, rects: Dict[str, Dict], svg_paths_dir: str) -> None:
        """Draw element distribution symbols in a grid."""
        # Load SVG files
        SVGPathService._load_svg_files(svg_paths_dir)
        
        # Get element distribution from stats
        distribution = stats.distribution('element')
        element_bodies = DistributionUtils.parse_distribution_bodies(distribution.grid)
        
        # Draw symbols for each element
        for element in ElementDistributionService.ELEMENTS:
            if element not in rects or element not in element_bodies:
                continue
                
            ElementDistributionService._draw_symbol_grid(
                draw=draw,
                bodies=element_bodies[element],
                rect=rects[element],
                rotation=ElementDistributionService.ELEMENT_ROTATIONS[element]
            ) 