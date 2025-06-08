"""
Element distribution service for Prof. Warlock.

Handles the rendering of element distribution (earth, water, fire, air) using SVG paths.
"""

import logging
from PIL import ImageDraw, Image
from typing import Dict, List
from natal.stats import Stats
from .svg_path_service import SVGPathService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElementDistributionService:
    """Service for handling element distribution visualization."""

    GRID_SIZE = (3, 3)  # 4x2 grid for up to 8 symbols per element
    ELEMENTS = ['fire', 'earth', 'air', 'water']
    
    # Fixed rotation angles for each element
    ELEMENT_ROTATIONS = {
        'earth': 45,
        'air': -45,
        'water': -135,
        'fire': 135
    }
    
    # Mapping natal library body names to symbol names
    BODY_TO_SYMBOL = {
        'sun': '☉', 'moon': '☽', 'mercury': '☿', 'venus': '♀', 'mars': '♂',
        'jupiter': '♃', 'saturn': '♄', 'uranus': '♅', 'neptune': '♆', 'pluto': '♇',
        'asc_node': '☊', 'asc': 'Asc', 'mc': 'MC'
    }

    @staticmethod
    def draw_element_distribution(draw: ImageDraw, stats: Stats, svg_paths_dir: str,
                                rects: Dict[str, Dict]) -> None:
        """Draw element distribution symbols in a grid."""
        SVGPathService._load_svg_files(svg_paths_dir)
        
        # Get element distribution from stats with 'element' kind
        distribution = stats.distribution('element')
        
        # Parse distribution grid to get bodies for each element
        element_bodies = {}
        for row in distribution.grid[1:]:  # Skip header row
            element = row[0].lower()  # Element name is in first column
            if element in ElementDistributionService.ELEMENTS:
                # Parse bodies from the 'bodies' column (last column)
                bodies_str = row[2]  # Bodies are in the third column
                # Split by comma and extract just the body name before the sign
                bodies = [body.split()[0].lower() for body in bodies_str.split(',')]
                element_bodies[element] = bodies
        
        # Draw symbols for each element
        for element in ElementDistributionService.ELEMENTS:
            if element not in rects or element not in element_bodies:
                continue

            rect = rects[element]
            bodies = element_bodies[element]
            
            # Create a temporary canvas for this element's grid
            grid_width = rect['width']
            grid_height = rect['height']
            grid_canvas = Image.new('RGBA', (int(grid_width), int(grid_height)), (0, 0, 0, 0))
            grid_draw = ImageDraw.Draw(grid_canvas)
            
            # Calculate cell dimensions
            cell_width = grid_width / ElementDistributionService.GRID_SIZE[0]
            cell_height = grid_height / ElementDistributionService.GRID_SIZE[1]
            
            # Draw each body's symbol in the grid
            for i, body in enumerate(bodies[:8]):  # Limit to 8 symbols
                if body not in ElementDistributionService.BODY_TO_SYMBOL:
                    continue
                    
                symbol = ElementDistributionService.BODY_TO_SYMBOL[body]
                row = i // ElementDistributionService.GRID_SIZE[0]
                col = i % ElementDistributionService.GRID_SIZE[0]
                
                # Calculate position in the temporary canvas
                x = col * cell_width + (cell_width / 2)
                y = row * cell_height + (cell_height / 2)
                
                if filename := SVGPathService._get_symbol_filename(symbol):
                    sym_img = SVGPathService.render_symbol(filename, size=int(cell_width * 1))
                    if sym_img:
                        # Center the symbol at (x,y)
                        px = int(x - sym_img.width / 2)
                        py = int(y - sym_img.height / 2)
                        grid_canvas.paste(sym_img, (px, py), sym_img)
            
            # Rotate the entire grid
            rotation = ElementDistributionService.ELEMENT_ROTATIONS[element]
            rotated_grid = grid_canvas.rotate(rotation, expand=True, resample=Image.BICUBIC)
            
            # Calculate paste position to center the rotated grid
            paste_x = int(rect['center_x'] - rotated_grid.width / 2)
            paste_y = int(rect['center_y'] - rotated_grid.height / 2)
            
            # Paste the rotated grid onto the main canvas
            draw._image.paste(rotated_grid, (paste_x, paste_y), rotated_grid) 