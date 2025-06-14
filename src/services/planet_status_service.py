"""
Planet status service for Prof. Warlock.

Handles retrograde and dignity indicators for planets in the natal chart.
"""

import os
import logging
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import cairosvg
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from natal import Data, Chart
from natal.stats import dignity_of, Stats
from .svg_path_service import SVGPathService
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlanetStatusService:
    # Common settings
    SYMBOL_SIZE = 40
    # Offset for retrograde symbol from planet position
    RETRO_OFFSET = 0  # pixels to offset the retrograde symbol


    @staticmethod
    def draw_planet_status(chart_image: Image.Image, svg_paths_dir: str, mimi: Data, stats: Stats) -> None:
        """Draw planet status indicators on the chart.
        
        Args:
            chart_image: The chart image to draw on
            svg_paths_dir: Directory containing SVG files
            mimi: The natal chart data
            stats: The stats object
        """
        # Calculate center and radius of the chart
        width, height = chart_image.size
        center_x = width // 2
        center_y = height // 2
        radius = min(width, height) // 2 - 530  # Leave some margin

        # Get celestial bodies from Stats
        celestial_data = stats.celestial_body
        
        # Draw status for each celestial body
        for row in celestial_data.grid[1:]:  # Skip header row
            name = row[0]
            parts = row[1].split(' ')
            degree_str = parts[0]
            sign = parts[1]
            minute_str = parts[2]
            is_retrograde = len(parts) > 3 and parts[3] == '℞'
            dignity = row[3]

            # Get planet angle from data
            planet = None
            for p in mimi.planets:
                if p.name == name:
                    planet = p
                    break
                    
            if not planet:
                continue
                
            print('PLANET', planet.name, SVGPathService.get_symbol(planet.name), planet.normalized_degree, planet.retro, planet.rx)
                
            # Get angle from planet's normalized_degree property (to match natal's SVG logic)
            angle = math.radians(planet.normalized_degree)
            x = center_x - radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Draw retrograde indicator with adjusted positioning
            if planet.retro:
                retrograde_img = SVGPathService.render_symbol('retrograde', PlanetStatusService.SYMBOL_SIZE)
                if retrograde_img:
                    # Calculate offset position based on angle
                    offset_x = PlanetStatusService.RETRO_OFFSET * math.cos(angle)
                    offset_y = PlanetStatusService.RETRO_OFFSET * math.sin(angle)
                    
                    # Apply offset and center the symbol around the point
                    symbol_x = int(x + offset_x - retrograde_img.size[0]/2)
                    symbol_y = int(y + offset_y - retrograde_img.size[1]/2)
                    
                    chart_image.paste(
                        retrograde_img,
                        (symbol_x, symbol_y),
                        retrograde_img
                    )

            # Draw dignity indicator
            if dignity:
                dignity = dignity.lower()
                dignity_img = SVGPathService.render_symbol(dignity, PlanetStatusService.SYMBOL_SIZE)
                if dignity_img:
                    
                    # Calculate offset position based on angle
                    offset_x =  math.cos(angle)
                    offset_y =  math.sin(angle)
                    
                    # Apply offset and center the symbol around the point
                    symbol_x = int(x + offset_x - retrograde_img.size[0]/2)
                    symbol_y = int(y + offset_y - retrograde_img.size[1]/2)
                    chart_image.paste(
                        dignity_img,
                        (symbol_x, symbol_y),
                        dignity_img
                    )

    @staticmethod
    def get_chart_with_status(data: Data, width: int = 2250, svg_paths_dir: str = None, chart: Chart = None, stats: Stats = None) -> Image.Image:
        """Get chart with retrograde and dignity indicators.
        
        Args:
            data: The natal chart data
            width: Chart width
            svg_paths_dir: Directory containing SVG files
            chart: The existing chart object
            stats: The existing stats object
            
        Returns:
            PIL Image object with the chart and status indicators
        """
        if not svg_paths_dir:
            svg_paths_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'assets', 'svg_paths')
        
        # Create chart with the data if not provided
        if not chart:
            chart = Chart(data1=data, width=width)
        
        # Get the chart's SVG and convert to PNG
        svg_str = chart.svg
        png_data = cairosvg.svg2png(bytestring=svg_str.encode('utf-8'))
        
        # Create PIL Image from PNG data
        chart_image = Image.open(BytesIO(png_data))
      
        
        # Draw planet status indicators
        PlanetStatusService.draw_planet_status(chart_image, svg_paths_dir, data, stats)
        
        return chart_image 