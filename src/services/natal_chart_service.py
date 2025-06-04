"""
Natal chart service for Prof. Warlock.

Parses user info and generates natal charts using the natal library.
"""

import re
from typing import Dict
from natal.chart import Chart
from io import BytesIO
from geopy.geocoders import Nominatim
from natal.data import Data
from datetime import datetime
import cairosvg
from PIL import Image, ImageDraw, ImageFont
import os
from natal.config import Config

class NatalChartService:
    @staticmethod
    def parse_user_info(body: str) -> Dict[str, str]:
        """Parse user info from email body in strict format."""
        # First try the original multiline pattern
        pattern = re.compile(r"^([A-Za-z ]+):\s*(.+)$", re.MULTILINE)
        matches = dict(pattern.findall(body))
        
        # If that didn't work (e.g., flattened email), try a more flexible pattern
        if len(matches) < 4:  # We need at least 4 fields
            # Look for field patterns anywhere in the text, not just at line starts
            pattern = re.compile(r"([A-Za-z ]+):\s*([^:\n\r]+?)(?=\s*[A-Za-z ]+:|$)")
            matches = dict(pattern.findall(body))
        
        required = ["First Name", "Last Name", "Date of Birth", "Place of Birth"]
        for field in required:
            if field not in matches:
                raise ValueError(f"Missing required field: {field}")
        
        # Clean up the values (remove trailing whitespace/junk)
        cleaned_matches = {}
        for key, value in matches.items():
            if key in required:
                cleaned_matches[key] = value.strip()
        
        return cleaned_matches

    @staticmethod
    def generate_chart(user_info: Dict[str, str]) -> bytes:
        """Generate a natal chart PNG using the natal library and return as bytes."""
        # Geocode place
        geolocator = Nominatim(user_agent="prof-warlock")
        location = geolocator.geocode(user_info["Place of Birth"])
        if not location:
            raise ValueError(f"Could not geocode location: {user_info['Place of Birth']}")
        lat, lon = location.latitude, location.longitude

        # Parse date (add time if not present)
        date_str = user_info["Date of Birth"]
        if len(date_str.strip().split()) == 1:
            date_str += " 00:00"
        try:
            dt = datetime.strptime(date_str, "%d-%m-%Y %H:%M")
            dt_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            raise ValueError("Date of Birth must be in DD-MM-YYYY format")

        # Use monochrome config for the chart
        mono_config = Config(theme_type="mono")
        data = Data(
            name=f"{user_info['First Name']} {user_info['Last Name']}",
            lat=lat,
            lon=lon,
            utc_dt=dt_str,
            config=mono_config
        )
        chart = Chart(data, width=2000)  # Render chart at 2000px for higher quality
        svg_str = chart.svg
        chart_png = cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), output_width=2000, output_height=2000)
        chart_img = Image.open(BytesIO(chart_png)).convert("RGBA")

        # A3 portrait: 2480x3508 px at 300dpi
        a3_width, a3_height = 2480, 3508
        canvas = Image.new("RGBA", (a3_width, a3_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(canvas)

        # Load fonts
        font_dir = os.path.join(os.path.dirname(__file__), '../../assets/fonts/static')
        font_bold = ImageFont.truetype(os.path.join(font_dir, 'Montserrat-Bold.ttf'), 140)
        font_regular = ImageFont.truetype(os.path.join(font_dir, 'Montserrat-Regular.ttf'), 54)
        font_light = ImageFont.truetype(os.path.join(font_dir, 'Montserrat-Light.ttf'), 36)

        # Top center: user name (larger)
        user_name = f"{user_info['First Name']} {user_info['Last Name']}"
        bbox = draw.textbbox((0, 0), user_name, font=font_bold)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((a3_width-w)//2, 120), user_name, font=font_bold, fill=(10, 10, 10, 255))

        # Below name: lat, long
        latlon = f"{lat:.4f}, {lon:.4f}"
        bbox = draw.textbbox((0, 0), latlon, font=font_regular)
        w, h2 = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((a3_width-w)//2, 150+h+20), latlon, font=font_regular, fill=(40, 40, 40, 255))

        # Center: natal chart (larger)
        chart_size = 2000
        chart_x = (a3_width - chart_size) // 2
        chart_y = 500
        chart_img = chart_img.resize((chart_size, chart_size), Image.LANCZOS)
        # To ensure monochrome, paste with a black mask if needed (chart is already mono)
        canvas.paste(chart_img, (chart_x, chart_y), chart_img)

        # Bottom left: birthday
        bday = user_info["Date of Birth"]
        bbox = draw.textbbox((0, 0), bday, font=font_regular)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((80, a3_height-220), bday, font=font_regular, fill=(30, 30, 30, 255))

        # Bottom right: birth place
        place = user_info["Place of Birth"]
        bbox = draw.textbbox((0, 0), place, font=font_regular)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((a3_width-w-80, a3_height-220), place, font=font_regular, fill=(30, 30, 30, 255))

        # Very bottom right: website
        website = "https://goker.art"
        bbox = draw.textbbox((0, 0), website, font=font_light)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((a3_width-w-80, a3_height-h-60), website, font=font_light, fill=(60, 60, 60, 255))

        # Save to bytes
        buf = BytesIO()
        canvas.save(buf, format="PNG")
        return buf.getvalue() 