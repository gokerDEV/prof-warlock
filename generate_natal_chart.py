#!/usr/bin/env python3

import argparse
from datetime import datetime
import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from src.services.natal_chart_service import NatalChartService

def main():
    parser = argparse.ArgumentParser(description='Generate a natal chart with given parameters')
    
    parser.add_argument('--name', required=True, help='First name')
    parser.add_argument('--surname', required=True, help='Last name')
    parser.add_argument('--birth-date', required=True, help='Birth date in DD-MM-YYYY format')
    parser.add_argument('--birth-time', required=True, help='Birth time in HH:MM format')
    parser.add_argument('--location', required=True, help='Birth location')
    parser.add_argument('--latitude', type=float, help='Latitude (optional if location is provided)')
    parser.add_argument('--longitude', type=float, help='Longitude (optional if location is provided)')
    parser.add_argument('--template', default='default', choices=['1', '2' ,'3'], help='Chart theme')
    parser.add_argument('--output', default='natal_chart.png', help='Output file path')
    
    args = parser.parse_args()
    
    # Combine date and time
    birth_datetime = f"{args.birth_date} {args.birth_time}"
    
    # Create user info dictionary
    user_info = {
        "First Name": args.name,
        "Last Name": args.surname,
        "Date of Birth": birth_datetime,
        "Place of Birth": args.location,
        "Latitude": args.latitude,
        "Longitude": args.longitude
    }
    
    # fcf2de
    try:
        # Generate the chart
        chart_service = NatalChartService()
        chart_bytes = chart_service.generate_chart(user_info, template=args.template, background_color="#ffffff")
        
        # Save the chart
        with open(args.output, 'wb') as f:
            f.write(chart_bytes)
            
        print(f"Natal chart has been generated successfully: {args.output}")
        
    except Exception as e:
        print(f"Error generating natal chart: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 