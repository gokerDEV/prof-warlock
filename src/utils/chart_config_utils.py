"""
Chart configuration utilities for Prof. Warlock.
"""

from natal.config import Config


class ChartConfigUtils:
    """Utility class for chart configuration management."""
    
    @staticmethod
    def configure_theme_settings(config: Config, background_color: str = "#ffffff") -> None:
        """
        Configure theme settings for charts.
        
        Args:
            config: The natal Config object to modify
            background_color: Background color for the chart
        """
        config.theme.background = background_color
        config.theme.foreground = "#393939"
        config.theme.fire = "#393939"
        config.theme.earth = "#393939"
        config.theme.air = "#393939"
        config.theme.water = "#393939"
        config.theme.points = "#393939"
        config.theme.asteroids = "#393939"
        config.theme.positive = "#393939"
        config.theme.negative = "#393939"
        config.theme.others = "#393939"
        config.theme.dim = background_color
        config.theme.transparency = 0  
    
    @staticmethod
    def configure_display_settings(config: Config, show_all: bool = True) -> None:
        """
        Configure display settings for celestial bodies.
        
        Args:
            config: The natal Config object to modify
            show_all: If True, show all celestial bodies. If False, show only main planets.
        """
        if show_all:
            # Show all celestial bodies
            config.display.sun = True
            config.display.moon = True
            config.display.mercury = True
            config.display.venus = True
            config.display.mars = True
            config.display.jupiter = True
            config.display.saturn = True
            config.display.uranus = True
            config.display.neptune = True
            config.display.pluto = True
            config.display.asc_node = True
            config.display.chiron = True
            config.display.ceres = True
            config.display.pallas = True
            config.display.juno = True
            config.display.vesta = True
            config.display.asc = True
            config.display.ic = True
            config.display.dsc = True
            config.display.mc = True
        else:
            # Show only main planets and essential points
            config.display.sun = True
            config.display.moon = True
            config.display.mercury = True
            config.display.venus = True
            config.display.mars = True
            config.display.jupiter = True
            config.display.saturn = True
            config.display.uranus = True
            config.display.neptune = True
            config.display.pluto = True
            config.display.asc_node = True
            config.display.chiron = False
            config.display.ceres = False
            config.display.pallas = False
            config.display.juno = False
            config.display.vesta = False
            config.display.asc = True
            config.display.ic = False
            config.display.dsc = False
            config.display.mc = True 