from natal.data import Data
import logging

logger = logging.getLogger(__name__)

class Zodiac:
    ZODIAC_SIGNS = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]

    def __init__(self, natal_data: Data):
        """
        Initialize Zodiac with existing natal Data object.
        
        Args:
            natal_data: Pre-calculated natal.data.Data object
        """
        try:
            if not isinstance(natal_data, Data):
                raise ValueError("natal_data must be a natal.data.Data object")
            
            self.data = natal_data
            logger.debug(f"Zodiac initialized with natal data for {natal_data.name}")
        except Exception as e:
            logger.error(f"Failed to initialize Zodiac: {str(e)}")
            raise ValueError(f"Failed to initialize Zodiac with natal data: {str(e)}")

    def _get_sign_from_planet(self, planet_name: str) -> str:
        """Helper method to get zodiac sign from a planet in natal data"""
        try:
            for planet in self.data.planets:
                if planet.name.lower() == planet_name:
                    return planet.sign.name
            logger.warning(f"Planet {planet_name} not found, falling back to aries")
            return "aries"  # fallback to aries if not found
        except Exception as e:
            logger.error(f"Error getting sign for planet {planet_name}: {str(e)}")
            return "aries"  # fallback to aries if error

    def get_sun_sign(self) -> str:
        """Get the sun sign"""
        return self._get_sign_from_planet("sun")

    def get_lunar_sign(self) -> str:
        """Get the moon sign"""
        return self._get_sign_from_planet("moon")

    def get_ascendant_sign(self) -> str:
        """Get the ascendant sign"""
        try:
            if self.data.asc and self.data.asc.sign:
                return self.data.asc.sign.name
            logger.warning("Ascendant sign not found, falling back to aries")
            return "aries"  # fallback to aries if not found
        except Exception as e:
            logger.error(f"Error getting ascendant sign: {str(e)}")
            return "aries"  # fallback to aries if error
    
    def get_chart_ruler(self) -> str:
        """Get the chart ruler"""
        try:
            if self.data.sun and self.data.sun.sign and self.data.sun.sign.classic_ruler:
                return self.data.sun.sign.classic_ruler
            logger.warning("Chart ruler not found, falling back to aries")
            return "aries"  # fallback to aries if not found
        except Exception as e:
            logger.error(f"Error getting chart ruler: {str(e)}")
            return "aries"  # fallback to aries if error

# # --- Example Usage ---
# # Create natal data first
# natal_data = Data(
#     name="Birth Chart",
#     lat=41.67,
#     lon=26.57,
#     utc_dt="1992-08-15 19:45"  # Already in UTC
# )

# # Pass it to Zodiac
# birth_chart = Zodiac(natal_data)

# sun_sign = birth_chart.get_sun_sign()
# lunar_sign = birth_chart.get_lunar_sign()
# ascendant_sign = birth_chart.get_ascendant_sign()

# print(f"Sun Sign: {sun_sign}")
# print(f"Lunar Sign: {lunar_sign}")
# print(f"Ascendant Sign: {ascendant_sign}")