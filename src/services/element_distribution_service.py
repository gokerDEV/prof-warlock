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
        'earth': 45,
        'air': -45,
        'water': -135,
        'fire': 135
    }

    # Colors
    SYMBOL_COLOR = "#393939"  # Same as DistributionService.BACKGROUND_COLOR

    @staticmethod
    def _draw_symbol_grid(draw: ImageDraw, bodies: List[str], rect: Dict, rotation: float) -> None:
        """Draw symbols in a grid with the specified rotation."""
        # Create a temporary canvas for this category's grid
        grid_width = rect['width']
        grid_height = rect['height']
        
        # Create canvas and calculate positions
        grid_canvas = DistributionUtils.create_grid_canvas(grid_width, grid_height)
        positions = DistributionUtils.calculate_grid_positions(grid_width, grid_height)
        
        # Draw each body's symbol in the grid
        for i, body in enumerate(bodies[:9]):  # Limit to 9 symbols (3x3 grid)
            if body not in DistributionUtils.BODY_TO_SYMBOL:
                continue
                
            symbol = DistributionUtils.BODY_TO_SYMBOL[body]
            x, y, cell_width, _ = positions[i]
            
            if sym_img := DistributionUtils.draw_symbol(symbol, size=int(cell_width * 1), color=ElementDistributionService.SYMBOL_COLOR):
                DistributionUtils.paste_centered(grid_canvas, sym_img, x, y)
        
        # Rotate the entire grid
        rotated_grid = grid_canvas.rotate(rotation, expand=True, resample=Image.BICUBIC)
        
        # Calculate paste position to center the rotated grid
        paste_x = int(rect['center_x'] - rotated_grid.width / 2)
        paste_y = int(rect['center_y'] - rotated_grid.height / 2)
        
        # Paste the rotated grid onto the main canvas
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