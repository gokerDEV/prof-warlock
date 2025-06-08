"""
Distribution utilities for Prof. Warlock.

Common utilities for handling distribution visualizations.
"""

import logging
from PIL import ImageDraw, Image, ImageFont
from typing import Dict, List
from .svg_path_service import SVGPathService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DistributionUtils:
    """Utility class for distribution services."""
    
    # Common symbol mapping
    BODY_TO_SYMBOL = {
        'sun': '☉', 'moon': '☽', 'mercury': '☿', 'venus': '♀', 'mars': '♂',
        'jupiter': '♃', 'saturn': '♄', 'uranus': '♅', 'neptune': '♆', 'pluto': '♇',
        'asc_node': '☊', 'asc': 'Asc', 'mc': 'MC'
    }
    
    # Common grid size
    GRID_SIZE = (3, 3)  # 3x3 grid for up to 9 symbols per category

    @staticmethod
    def parse_distribution_bodies(distribution_grid: List[List[str]], skip_header: bool = True) -> Dict[str, List[str]]:
        """Parse distribution grid to get bodies for each category."""
        category_bodies = {}
        start_idx = 1 if skip_header else 0
        
        for row in distribution_grid[start_idx:]:
            category = row[0].lower()  # Category name is in first column
            # Parse bodies from the 'bodies' column (last column)
            bodies_str = row[2]  # Bodies are in the third column
            # Split by comma and extract just the body name before the sign
            bodies = [body.split()[0].lower() for body in bodies_str.split(',')]
            category_bodies[category] = bodies
            
        return category_bodies

    @staticmethod
    def draw_symbol(symbol: str, size: int, color: str = None) -> Image.Image:
        """Draw a single symbol with the specified size and color."""
        if filename := SVGPathService._get_symbol_filename(symbol):
            return SVGPathService.render_symbol(filename, size=size, color=color)
        return None

    @staticmethod
    def calculate_grid_positions(grid_width: int, grid_height: int) -> List[tuple]:
        """Calculate positions for symbols in a grid."""
        positions = []
        cell_width = grid_width / DistributionUtils.GRID_SIZE[0]
        cell_height = grid_height / DistributionUtils.GRID_SIZE[1]
        
        for i in range(DistributionUtils.GRID_SIZE[0] * DistributionUtils.GRID_SIZE[1]):
            row = i // DistributionUtils.GRID_SIZE[0]
            col = i % DistributionUtils.GRID_SIZE[0]
            
            x = col * cell_width + (cell_width / 2)
            y = row * cell_height + (cell_height / 2)
            positions.append((x, y, cell_width, cell_height))
            
        return positions

    @staticmethod
    def create_grid_canvas(width: int, height: int, background_color: str = None) -> Image.Image:
        """Create a new canvas for grid with optional background color."""
        if background_color:
            # Convert hex color to RGBA
            r = int(background_color[1:3], 16)
            g = int(background_color[3:5], 16)
            b = int(background_color[5:7], 16)
            return Image.new('RGBA', (int(width), int(height)), (r, g, b, 255))
        return Image.new('RGBA', (int(width), int(height)), (0, 0, 0, 0))

    @staticmethod
    def paste_centered(canvas: Image.Image, img: Image.Image, x: float, y: float) -> None:
        """Paste an image centered at the specified position."""
        px = int(x - img.width / 2)
        py = int(y - img.height / 2)
        canvas.paste(img, (px, py), img) 