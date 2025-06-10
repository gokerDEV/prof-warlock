"""
Aspect matrix service for Prof. Warlock.

Handles the rendering of aspect matrix using SVG paths.
"""

import logging
from PIL import Image, ImageDraw
from typing import List
from .svg_path_service import SVGPathService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AspectMatrixService:
    TOP = 2600

    @staticmethod
    def draw_aspect_matrix(draw: ImageDraw, grid: List[List[str]], width: int, svg_paths_dir: str) -> None:
        """
        Draws the aspect matrix based on the specified rotation logic.
        1. Creates a lower-triangle matrix with labels.
        2. Pre-rotates individual elements (icons and labels).
        3. Rotates the entire canvas.
        """
        SVGPathService._load_svg_files(svg_paths_dir)
        
        grid = [row[:] for row in AspectMatrixService._remove_sum_column(grid)]
        if not grid or not grid[0]:
            return
        
        size = len(grid[0])
        cell = SVGPathService.CELL_SIZE
        icon_size = int(cell * 0.8)  
        label_size = int(cell * 0.8)  
        planet_row = grid[0] 

        canvas_dim = (size + 1) * cell
        matrix_canvas = Image.new('RGBA', (canvas_dim, canvas_dim), (0, 0, 0, 0))
        matrix_draw = ImageDraw.Draw(matrix_canvas)

        # Draw matrix cells and icons
        for i in range(1,size):
            for j in range(i - 1):
                x = (j + 1) * cell 
                y = i * cell
                
                matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                    outline=SVGPathService.BORDER_COLOR,
                                    width=SVGPathService.BORDER_WIDTH)
                
                # Use grid[i][j+1] to skip the first column which contains row labels
                symbol_char = grid[i][j+1].strip() if j+1 < len(grid[i]) else ""
                if symbol_char and (filename := SVGPathService._get_symbol_filename(symbol_char)):
                    sym_img = SVGPathService.render_symbol(filename, size=icon_size)
                    if sym_img:
                        rotated_sym = sym_img.rotate(135, expand=True, resample=Image.BICUBIC)
                        px = x + (cell - rotated_sym.width) // 2
                        py = y + (cell - rotated_sym.height) // 2
                        matrix_canvas.paste(rotated_sym, (px, py), rotated_sym)

        # Draw row labels (left side)
        for i in range(2, size):
            x = 0
            y = i * cell
            matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                outline=SVGPathService.BORDER_COLOR,
                                width=SVGPathService.BORDER_WIDTH)
            
            symbol_char = planet_row[i].strip()
            if symbol_char and (filename := SVGPathService._get_symbol_filename(symbol_char)):
                label_img = SVGPathService.render_symbol(filename, size=label_size)
                if label_img:
                    rotated_label = label_img.rotate(90, expand=True, resample=Image.BICUBIC)
                    px = x + (cell - rotated_label.width) // 2
                    py = y + (cell - rotated_label.height) // 2
                    matrix_canvas.paste(rotated_label, (px, py), rotated_label)

        # Draw column labels (bottom)
        for j in range(1,size-1):
            x = j * cell
            y = size * cell
            matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                outline=SVGPathService.BORDER_COLOR,
                                width=SVGPathService.BORDER_WIDTH)
            
            symbol_char = planet_row[j].strip()
            if symbol_char and (filename := SVGPathService._get_symbol_filename(symbol_char)):
                label_img = SVGPathService.render_symbol(filename, size=label_size)
                if label_img:
                    rotated_label = label_img.rotate(180, expand=True, resample=Image.BICUBIC)
                    px = x + (cell - rotated_label.width) // 2
                    py = y + (cell - rotated_label.height) // 2
                    matrix_canvas.paste(rotated_label, (px, py), rotated_label)

        final_image = matrix_canvas.rotate(-135, expand=True, resample=Image.BICUBIC)

        paste_x = (width - final_image.width) // 2
        paste_y = 2260
        draw._image.paste(final_image, (paste_x, paste_y), final_image)

    @staticmethod
    def _remove_sum_column(grid: List[List[str]]) -> List[List[str]]:
        """Remove the 'sum' column from the grid."""
        if grid and grid[0] and 'sum' in grid[0][-1].lower():
             return [row[:-1] for row in grid]
        return grid