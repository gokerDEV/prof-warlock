from datetime import datetime, timezone, timedelta
from natal.data import Data
import logging

logger = logging.getLogger(__name__)

class Zodiac:
    ZODIAC_SIGNS = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]

    def __init__(self, year: int, month: int, day: int, hour: int, minute: int,
                 latitude: float, longitude: float, utc_offset: int = 3):
        try:
            # Create naive datetime first
            local_dt = datetime(year, month, day, hour, minute)
            
            # Convert to UTC
            utc_dt = local_dt - timedelta(hours=utc_offset)
            
            # Format for natal library
            utc_str = utc_dt.strftime("%Y-%m-%d %H:%M")
            
            logger.debug(f"Local datetime: {local_dt}, UTC datetime: {utc_dt}")
            
            # Create natal Data object
            self.data = Data(
                name="temp",  # temporary name since we only need zodiac info
                utc_dt=utc_str,
                lat=latitude,
                lon=longitude
            )
        except Exception as e:
            logger.error(f"Failed to initialize Zodiac: {str(e)}")
            raise ValueError(f"Failed to initialize Zodiac with date {year}-{month}-{day} {hour}:{minute}: {str(e)}")

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
# birth_chart = Zodiac(
#     year=1992,
#     month=8,
#     day=15,
#     hour=22,
#     minute=45,
#     latitude=41.67,
#     longitude=26.57,
#     utc_offset=3
# )

# sun_sign = birth_chart.get_sun_sign()
# lunar_sign = birth_chart.get_lunar_sign()
# ascendant_sign = birth_chart.get_ascendant_sign()

# print(f"Sun Sign: {sun_sign}")
# print(f"Lunar Sign: {lunar_sign}")
# print(f"Ascendant Sign: {ascendant_sign}")