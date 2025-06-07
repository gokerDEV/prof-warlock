from datetime import datetime, timezone, timedelta
from natal.data import Data

class Zodiac:
    ZODIAC_SIGNS = [
        "aries", "taurus", "gemini", "cancer", "leo", "virgo",
        "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
    ]

    def __init__(self, year: int, month: int, day: int, hour: int, minute: int,
                 latitude: float, longitude: float, utc_offset: int = 3):
        
        # Convert local time to UTC
        local_dt = datetime(year, month, day, hour, minute, tzinfo=timezone(timedelta(hours=utc_offset)))
        utc_dt = local_dt.astimezone(timezone.utc)
        
        # Create natal Data object
        self.data = Data(
            name="temp",  # temporary name since we only need zodiac info
            utc_dt=utc_dt.strftime("%Y-%m-%d %H:%M"),
            lat=latitude,
            lon=longitude
        )

    def _get_sign_from_planet(self, planet_name: str) -> str:
        """Helper method to get zodiac sign from a planet in natal data"""
        for planet in self.data.planets:
            if planet.name.lower() == planet_name:
                return planet.sign.name
        return "aries"  # fallback to aries if not found

    def get_sun_sign(self) -> str:
        """Get the sun sign"""
        return self._get_sign_from_planet("sun")

    def get_lunar_sign(self) -> str:
        """Get the moon sign"""
        return self._get_sign_from_planet("moon")

    def get_ascendant_sign(self) -> str:
        """Get the ascendant sign"""
        if self.data.asc:
            return self.data.asc.sign.name
        return "aries"  # fallback to aries if not found

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