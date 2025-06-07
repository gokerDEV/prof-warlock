import os
import re
import logging
from pathlib import Path
from PIL import Image, ImageDraw
from io import BytesIO
import cairosvg
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AspectMatrixService:
    CELL_SIZE = 80   # Fixed cell size 80x80
    BORDER_COLOR = (0, 0, 0, 255)  # Black color for borders
    BORDER_WIDTH = 2  # Border width for visibility
    TOP = 2600

    # Mapping for all symbols to file names
    SYMBOL_MAP = {
        '☉': 'sun', '☽': 'moon', '☿': 'mercury', '♀': 'venus', '♂': 'mars',
        '♃': 'jupiter', '♄': 'saturn', '♅': 'uranus', '♆': 'neptune', '♇': 'pluto',
        '☊': 'asc_node', 'Asc': 'asc', 'MC': 'mc',
        '☌': 'conjunction', '□': 'square', '△': 'trine', '⚹': 'sextile',
        '⚺': 'quincunx', '☍': 'opposition', '⚻': 'semisextile',
        '⚼': 'sesquiquadrate', '∠': 'semisquare',
    }

    _svg_cache: Dict[str, str] = {}

    @staticmethod
    def _load_svg_files(svg_paths_dir: str) -> None:
        """Load all SVG files into memory once."""
        if not AspectMatrixService._svg_cache:
            for symbol, filename in AspectMatrixService.SYMBOL_MAP.items():
                path = os.path.join(svg_paths_dir, f"{filename}.svg")
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        AspectMatrixService._svg_cache[filename] = f.read()
                else:
                    logger.warning(f"SVG file not found: {path}")

    @staticmethod
    def _get_symbol_filename(symbol: str) -> str:
        """Convert any symbol to its corresponding file name."""
        return AspectMatrixService.SYMBOL_MAP.get(symbol.strip(), '')

    @staticmethod
    def _remove_sum_column(grid: List[List[str]]) -> List[List[str]]:
        """Remove the 'sum' column from the grid."""
        if grid and grid[0] and 'sum' in grid[0][-1].lower():
             return [row[:-1] for row in grid]
        return grid

    @staticmethod
    def _render_symbol(filename: str, size: int) -> Image.Image:
        """Renders the SVG from the given filename into a PNG image of the desired size."""
        if filename in AspectMatrixService._svg_cache:
            path_content = AspectMatrixService._svg_cache[filename]
            
            # Create a complete SVG structure with larger viewBox
            svg_template = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 50 50">
    <g transform="translate(2,2) scale(2,2)" stroke="black" stroke-width="1.5" fill="none">
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

    @staticmethod
    def draw_aspect_matrix(draw: ImageDraw, grid: List[List[str]], width: int, svg_paths_dir: str) -> None:
        """
        Draws the aspect matrix based on the specified rotation logic.
        1. Creates a lower-triangle matrix with labels.
        2. Pre-rotates individual elements (icons and labels).
        3. Rotates the entire canvas.
        """
        AspectMatrixService._load_svg_files(svg_paths_dir)
        
        grid = [row[:] for row in AspectMatrixService._remove_sum_column(grid)]
        if not grid or not grid[0]:
            return
        
        size = len(grid[0])
        cell = AspectMatrixService.CELL_SIZE
        icon_size = int(cell * 0.8)  
        label_size = int(cell * 0.8)  
        planet_row = grid[0] 

        canvas_dim = (size + 1) * cell
        matrix_canvas = Image.new('RGBA', (canvas_dim, canvas_dim), (0, 0, 0, 0))
        matrix_draw = ImageDraw.Draw(matrix_canvas)

        # Draw matrix cells and icons
        for i in range(size):
            for j in range(i - 1):
                x = (j + 1) * cell 
                y = i * cell
                
                matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                    outline=AspectMatrixService.BORDER_COLOR,
                                    width=AspectMatrixService.BORDER_WIDTH)
                
                # Use grid[i][j+1] to skip the first column which contains row labels
                symbol_char = grid[i][j+1].strip() if j+1 < len(grid[i]) else ""
                if symbol_char and (filename := AspectMatrixService._get_symbol_filename(symbol_char)):
                    sym_img = AspectMatrixService._render_symbol(filename, size=icon_size)
                    if sym_img:
                        rotated_sym = sym_img.rotate(135, expand=True, resample=Image.BICUBIC)
                        px = x + (cell - rotated_sym.width) // 2
                        py = y + (cell - rotated_sym.height) // 2
                        matrix_canvas.paste(rotated_sym, (px, py), rotated_sym)

        # Draw row labels (left side)
        for i in range(size):
            x = 0
            y = i * cell
            matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                outline=AspectMatrixService.BORDER_COLOR,
                                width=AspectMatrixService.BORDER_WIDTH)
            
            symbol_char = planet_row[i].strip()
            if symbol_char and (filename := AspectMatrixService._get_symbol_filename(symbol_char)):
                label_img = AspectMatrixService._render_symbol(filename, size=label_size)
                if label_img:
                    rotated_label = label_img.rotate(90, expand=True, resample=Image.BICUBIC)
                    px = x + (cell - rotated_label.width) // 2
                    py = y + (cell - rotated_label.height) // 2
                    matrix_canvas.paste(rotated_label, (px, py), rotated_label)

        # Draw column labels (bottom)
        for j in range(size):
            x = j * cell
            y = size * cell
            matrix_draw.rectangle([x, y, x + cell, y + cell], 
                                outline=AspectMatrixService.BORDER_COLOR,
                                width=AspectMatrixService.BORDER_WIDTH)
            
            symbol_char = planet_row[j].strip()
            if symbol_char and (filename := AspectMatrixService._get_symbol_filename(symbol_char)):
                label_img = AspectMatrixService._render_symbol(filename, size=label_size)
                if label_img:
                    rotated_label = label_img.rotate(180, expand=True, resample=Image.BICUBIC)
                    px = x + (cell - rotated_label.width) // 2
                    py = y + (cell - rotated_label.height) // 2
                    matrix_canvas.paste(rotated_label, (px, py), rotated_label)

        final_image = matrix_canvas.rotate(-135, expand=True, resample=Image.BICUBIC)

        paste_x = (width - final_image.width) // 2
        paste_y = 2260
        draw._image.paste(final_image, (paste_x, paste_y), final_image)