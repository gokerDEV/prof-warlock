"""
FastAPI application for Prof. Warlock.

Clean, focused API with proper error handling and security.
"""

import logging
from fastapi import FastAPI, HTTPException, Request, Query, Depends, Header, Response
from fastapi.responses import JSONResponse
from typing import Optional, Dict
from datetime import datetime
import base64
from PIL import Image
import io
import boto3
from hashlib import sha256
import hashlib
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from .. import __version__

from ..core.configuration import config
from ..core.domain_models import (
    NatalChartRequest, 
    NatalStatsRequest,
    NatalTransitRequest,
    NatalTransitLocationRequest,
    NatalTransitRelocationRequest
)

from ..services.natal_chart_service import NatalChartService

APP_VERSION = __version__


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Prof. Warlock",
    description="Natal Chart Poster Generator via Email",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize services
natal_chart_service = NatalChartService()

# Initialize S3 client
s3_client = boto3.client(
    's3',
    region_name=config.s3.REGION,
    aws_access_key_id=config.s3.ACCESS_KEY_ID,
    aws_secret_access_key=config.s3.SECRET_ACCESS_KEY
)

# Initialize MongoDB client
mongodb_client = AsyncIOMotorClient(config.mongodb.uri)
mongodb_db = mongodb_client[config.mongodb.DATABASE]
natal_collection = mongodb_db.natal
natal_daily_collection = mongodb_db.natal_daily

# Create indexes for better performance
async def create_indexes():
    """Create necessary indexes for optimal performance."""
    try:
        # Create compound index for natal_daily collection with type field for proper caching
        # This allows different chart types (classic, location, relocation) for the same date
        await natal_daily_collection.create_index([("natal_id", 1), ("type", 1), ("date", 1)], unique=True)
        
        # Create TTL index for automatic cleanup of old cache entries (2 days)
        await natal_daily_collection.create_index([("created_at", 1)], expireAfterSeconds=172800)  # 2 days = 172800 seconds
        
        logger.info("📇 Created indexes for natal_daily collection")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    await create_indexes()





async def verify_api_key(x_api_key: str = Header(..., alias="X-Api-Key")) -> str:
    """
    Verify API key from header.
    
    Args:
        x_api_key: API key from X-Api-Key header
        
    Returns:
        str: Verified API key
        
    Raises:
        HTTPException: If API key is invalid or missing
    """    
    if not x_api_key or x_api_key != config.security.API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing API key"
        )
    return x_api_key


async def get_or_generate_daily_stats(
    mongo_id: str,
    birth_day: int,
    birth_month: int, 
    birth_year: int,
    birth_time: str,
    birth_place: str,
    latitude: Optional[float],
    longitude: Optional[float],
    timezone: Optional[str],
    today_date: str
) -> Dict:
    """
    Get daily stats from cache or generate new ones.
    
    Args:
        mongo_id: MongoDB natal chart document ID
        birth_day, birth_month, birth_year: Birth date components
        birth_time: Birth time in HH:MM format
        birth_place: Birth place
        latitude, longitude: Birth coordinates
        timezone: Timezone offset
        today_date: Today's date in YYYY-MM-DD format
        
    Returns:
        Dict: Daily stats data
    """
    try:
        # Check if daily stats already exist for today
        daily_query = {
            "natal_id": mongo_id,
            "date": today_date
        }
        
        logger.info(f"🔍 Checking daily stats cache for {mongo_id} on {today_date}")
        existing_stats = await natal_daily_collection.find_one(daily_query)
        
        if existing_stats:
            logger.info(f"📊 Using cached daily stats for {mongo_id} on {today_date}")
            # Return cached stats (remove MongoDB _id)
            stats_data = existing_stats.copy()
            stats_data.pop("_id", None)
            stats_data.pop("natal_id", None)
            stats_data.pop("date", None)
            stats_data.pop("created_at", None)
            return stats_data
        
        # Generate new daily stats
        logger.info(f"📊 Generating new daily stats for {mongo_id} on {today_date}")
        
        # Get current time
        current_time = datetime.now().strftime("%H:%M")
        
        # Generate natal stats
        logger.info(f"⭐ Calling natal_chart_service.get_natal_stats...")
        stats_data = await natal_chart_service.get_natal_stats(
            birth_datetime=f"{birth_day:02d}-{birth_month:02d}-{birth_year} {birth_time}",
            birth_place=birth_place,
            latitude=latitude,
            longitude=longitude,
            today_date=datetime.now().strftime("%d-%m-%Y"),
            today_time=current_time,
            timezone=timezone
        )
        
        logger.info(f"⭐ Received stats_data: {type(stats_data)}")
        
        # Cache the daily stats
        daily_document = {
            "natal_id": mongo_id,
            "date": today_date,
            "created_at": datetime.now(),
            **stats_data
        }
        
        logger.info(f"💾 Inserting daily stats to MongoDB for {mongo_id} on {today_date}")
        logger.info(f"💾 Document to insert: {daily_document}")
        
        insert_result = await natal_daily_collection.insert_one(daily_document)
        logger.info(f"💾 Insert result: {insert_result.inserted_id}")
        
        # Verify insertion
        verification_query = {
            "natal_id": mongo_id,
            "date": today_date
        }
        verified_doc = await natal_daily_collection.find_one(verification_query)
        if verified_doc:
            logger.info(f"✅ Successfully cached daily stats for {mongo_id} on {today_date}")
        else:
            logger.error(f"❌ Failed to verify cached daily stats for {mongo_id} on {today_date}")
        
        return stats_data
        
    except Exception as e:
        logger.error(f"💥 Error getting/generating daily stats: {str(e)}")
        logger.error(f"💥 Exception type: {type(e)}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        # Return empty stats on error
        return {
            "full_report": "Error generating daily stats",
            "sun_sign": "unknown",
            "moon_sign": "unknown", 
            "rising_sign": "unknown"
        }


async def validate_birth_info(mongo_id: str, birth_day: int, birth_month: int, birth_year: int, birth_time: str) -> dict:
    """
    Validate birth information against stored data for security.
    
    Args:
        mongo_id: MongoDB document ID
        birth_day, birth_month, birth_year: Birth date components
        birth_time: Birth time in HH:MM format
        
    Returns:
        dict: Natal chart document if valid
        
    Raises:
        HTTPException: If validation fails
    """
    # Validate MongoDB ID format
    if not ObjectId.is_valid(mongo_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid MongoDB ID format"
        )
    
    # Query MongoDB with ID and birth information for security
    query = {
        "_id": ObjectId(mongo_id),
        "birth_day": birth_day,
        "birth_month": birth_month,
        "birth_year": birth_year,
        "birth_time": birth_time
    }
    
    document = await natal_collection.find_one(query)
    
    if not document:
        raise HTTPException(
            status_code=403,
            detail="Birth information doesn't match or natal chart not found"
        )
    
    return document


async def check_premium_access(document: dict) -> bool:
    """
    Check if user has premium access.
    
    Args:
        document: Natal chart document from MongoDB
        
    Returns:
        bool: True if user has premium access
        
    Raises:
        HTTPException: If premium access is required but not available
    """
    purchased = document.get("purchased", False)
    
    if not purchased:
        raise HTTPException(
            status_code=402,
            detail="Premium access required for this feature"
        )
    
    return True


async def get_or_generate_transit_cache(
    mongo_id: str,
    chart_type: str,
    birth_document: dict,
    today_date: str,
    today_time: str,
    location_params: dict = None
) -> dict:
    """
    Get transit data from cache or generate new ones.
    
    Args:
        mongo_id: MongoDB natal chart document ID
        chart_type: Type of chart ("classic", "location", "relocation")
        birth_document: Birth information document
        today_date: Today's date in YYYY-MM-DD format
        today_time: Today's time in HH:MM format
        location_params: Additional location parameters for premium features
        
    Returns:
        dict: {"chart_data": transit_data, "daily_record_id": str(mongo_id)}
    """
    try:
        # Check if transit data already exists for today
        cache_query = {
            "natal_id": mongo_id,
            "type": chart_type,
            "date": today_date
        }
        
        logger.info(f"🔍 Checking transit cache for {mongo_id} type {chart_type} on {today_date}")
        existing_cache = await natal_daily_collection.find_one(cache_query)
        
        if existing_cache:
            logger.info(f"📊 Using cached transit data for {mongo_id} type {chart_type} on {today_date}")
            # Return cached data with daily record ID
            chart_data = existing_cache.get("chart_data", {})
            daily_record_id = str(existing_cache["_id"])
            return {"chart_data": chart_data, "daily_record_id": daily_record_id}
        
        # Generate new transit data
        logger.info(f"📊 Generating new transit data for {mongo_id} type {chart_type} on {today_date}")
        
        # Prepare birth datetime
        birth_datetime = f"{birth_document['birth_day']:02d}-{birth_document['birth_month']:02d}-{birth_document['birth_year']} {birth_document['birth_time']}"
        
        # Generate transit data based on chart type
        if chart_type == "classic":
            # Generate classic transit data using the same approach as daily image
            logger.info(f"🔄 Generating classic transit data for {mongo_id}")
            
            try:
                from natal.data import Data
                from natal.config import Config
                from natal.stats import Stats
                from datetime import datetime
                
                # Parse dates
                birth_dt = datetime.strptime(birth_datetime, "%d-%m-%Y %H:%M")
                today_dt = datetime.strptime(f"{'-'.join(today_date.split('-')[::-1])} {today_time}", "%d-%m-%Y %H:%M")
                
                # Convert to UTC if timezone is provided
                if birth_document.get("timezone"):
                    from pytz import timezone
                    tz = timezone(birth_document.get("timezone"))
                    birth_utc_dt = tz.localize(birth_dt).astimezone(timezone('UTC')).replace(tzinfo=None)
                    today_utc_dt = tz.localize(today_dt).astimezone(timezone('UTC')).replace(tzinfo=None)
                else:
                    birth_utc_dt = birth_dt
                    today_utc_dt = today_dt
                
                # Get birth location coordinates
                birth_lat = birth_document.get("latitude")
                birth_lon = birth_document.get("longitude")
                
                # Create both natal and transit data at birth location for classic
                natal_data = Data(
                    name="Natal",
                    lat=birth_lat,
                    lon=birth_lon,
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                transit_data_obj = Data(
                    name="Transit",
                    lat=birth_lat,
                    lon=birth_lon,
                    utc_dt=today_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Calculate stats between birth location natal and birth location transits
                stats = Stats(data1=natal_data, data2=transit_data_obj)
                
                # Initialize Zodiac service with natal data
                from src.services.zodiac_service import Zodiac
                zodiac = Zodiac(natal_data)
                
                # Get zodiac signs from natal data
                sun_sign = zodiac.get_sun_sign()
                moon_sign = zodiac.get_lunar_sign()
                ascendant_sign = zodiac.get_ascendant_sign()
                
                # Generate full report
                try:
                    full_report_markdown = stats.full_report(kind="markdown")
                    if isinstance(full_report_markdown, bytes):
                        full_report_markdown = full_report_markdown.decode('utf-8', errors='ignore')
                    full_report_markdown = full_report_markdown.encode('utf-8', errors='ignore').decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to generate full report: {e}")
                    full_report_markdown = "Report generation failed due to encoding issues."
                
                # Create the transit_data dict
                transit_data = {
                    "full_report": full_report_markdown,
                    "sun_sign": sun_sign,
                    "moon_sign": moon_sign,
                    "rising_sign": ascendant_sign
                }
                
                logger.info(f"🔄 Generated classic transit data keys: {list(transit_data.keys())}")
                logger.info(f"🔄 Sun sign: {transit_data.get('sun_sign')}")
                logger.info(f"🔄 Full report length: {len(transit_data.get('full_report', ''))}")
                
            except Exception as stats_error:
                logger.error(f"🔄 Error in classic transit generation: {str(stats_error)}")
                import traceback
                logger.error(f"🔄 Classic traceback: {traceback.format_exc()}")
                raise stats_error
        elif chart_type == "location":
            # Generate location-based transit data using current location for transits
            # For location-based charts: natal at birth location, transits at current location
            logger.info(f"🔄 Generating location transit data for {mongo_id}")
            logger.info(f"🔄 Birth location: {birth_document.get('birth_place')}")
            logger.info(f"🔄 Current location: {location_params.get('current_location')}")
            logger.info(f"🔄 Current latitude: {location_params.get('current_latitude')}")
            logger.info(f"🔄 Current longitude: {location_params.get('current_longitude')}")
            
            try:
                # Create a custom location-based transit calculation
                # This requires manually creating the Data objects with different locations
                from natal.data import Data
                from natal.config import Config
                from natal.stats import Stats
                from datetime import datetime
                
                # Parse dates
                birth_dt = datetime.strptime(birth_datetime, "%d-%m-%Y %H:%M")
                today_dt = datetime.strptime(f"{'-'.join(today_date.split('-')[::-1])} {today_time}", "%d-%m-%Y %H:%M")
                
                # Convert to UTC if timezone is provided
                if birth_document.get("timezone"):
                    birth_utc_dt = natal_chart_service._convert_local_to_utc(birth_dt, birth_document.get("timezone"))
                    today_utc_dt = natal_chart_service._convert_local_to_utc(today_dt, birth_document.get("timezone"))
                else:
                    birth_utc_dt = birth_dt
                    today_utc_dt = today_dt
                
                # Get birth location coordinates
                birth_lat = birth_document.get("latitude")
                birth_lon = birth_document.get("longitude")
                if birth_lat is None or birth_lon is None:
                    from geopy.geocoders import Nominatim
                    geolocator = Nominatim(user_agent="prof-warlock")
                    birth_location = geolocator.geocode(birth_document.get("birth_place"))
                    if birth_location:
                        birth_lat, birth_lon = birth_location.latitude, birth_location.longitude
                    else:
                        raise ValueError(f"Could not geocode birth place: {birth_document.get('birth_place')}")
                
                # Get current location coordinates
                current_lat = location_params.get("current_latitude")
                current_lon = location_params.get("current_longitude")
                if current_lat is None or current_lon is None:
                    from geopy.geocoders import Nominatim
                    geolocator = Nominatim(user_agent="prof-warlock")
                    current_location = geolocator.geocode(location_params.get("current_location"))
                    if current_location:
                        current_lat, current_lon = current_location.latitude, current_location.longitude
                    else:
                        raise ValueError(f"Could not geocode current location: {location_params.get('current_location')}")
                
                # Create natal data at birth location
                natal_data = Data(
                    name="Natal",
                    lat=birth_lat,
                    lon=birth_lon,
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Create transit data at current location
                transit_data_obj = Data(
                    name="Transit",
                    lat=current_lat,
                    lon=current_lon,
                    utc_dt=today_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Calculate stats between birth location natal and current location transits
                stats = Stats(data1=natal_data, data2=transit_data_obj)
                
                # Initialize Zodiac service with natal data
                from src.services.zodiac_service import Zodiac
                zodiac = Zodiac(natal_data)
                
                # Get zodiac signs from natal data
                sun_sign = zodiac.get_sun_sign()
                moon_sign = zodiac.get_lunar_sign()
                ascendant_sign = zodiac.get_ascendant_sign()
                
                # Generate full report
                try:
                    full_report_markdown = stats.full_report(kind="markdown")
                    if isinstance(full_report_markdown, bytes):
                        full_report_markdown = full_report_markdown.decode('utf-8', errors='ignore')
                    full_report_markdown = full_report_markdown.encode('utf-8', errors='ignore').decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to generate full report: {e}")
                    full_report_markdown = "Report generation failed due to encoding issues."
                
                # Create the transit_data dict
                transit_data = {
                    "full_report": full_report_markdown,
                    "sun_sign": sun_sign,
                    "moon_sign": moon_sign,
                    "rising_sign": ascendant_sign
                }
                
                logger.info(f"🔄 Generated location transit data keys: {list(transit_data.keys())}")
                logger.info(f"🔄 Sun sign: {transit_data.get('sun_sign')}")
                logger.info(f"🔄 Full report length: {len(transit_data.get('full_report', ''))}")
                
            except Exception as stats_error:
                logger.error(f"🔄 Error in location get_natal_stats: {str(stats_error)}")
                import traceback
                logger.error(f"🔄 Location traceback: {traceback.format_exc()}")
                raise stats_error
            
        elif chart_type == "relocation":
            # Generate relocation-based transit data using relocated birth location
            # For relocation charts: natal as if born at relocated location, transits at relocated location
            logger.info(f"🔄 Generating relocation transit data for {mongo_id}")
            logger.info(f"🔄 Original birth location: {birth_document.get('birth_place')}")
            logger.info(f"🔄 Relocation location: {location_params.get('relocation_location')}")
            logger.info(f"🔄 Relocation latitude: {location_params.get('relocation_latitude')}")
            logger.info(f"🔄 Relocation longitude: {location_params.get('relocation_longitude')}")
            
            try:
                # Create a custom relocation-based transit calculation
                # This calculates the natal chart as if born at the relocated location
                from natal.data import Data
                from natal.config import Config
                from natal.stats import Stats
                from datetime import datetime
                
                # Parse dates
                birth_dt = datetime.strptime(birth_datetime, "%d-%m-%Y %H:%M")
                today_dt = datetime.strptime(f"{'-'.join(today_date.split('-')[::-1])} {today_time}", "%d-%m-%Y %H:%M")
                
                # Convert to UTC if timezone is provided
                if birth_document.get("timezone"):
                    birth_utc_dt = natal_chart_service._convert_local_to_utc(birth_dt, birth_document.get("timezone"))
                    today_utc_dt = natal_chart_service._convert_local_to_utc(today_dt, birth_document.get("timezone"))
                else:
                    birth_utc_dt = birth_dt
                    today_utc_dt = today_dt
                
                # Get relocation coordinates
                relocation_lat = location_params.get("relocation_latitude")
                relocation_lon = location_params.get("relocation_longitude")
                if relocation_lat is None or relocation_lon is None:
                    from geopy.geocoders import Nominatim
                    geolocator = Nominatim(user_agent="prof-warlock")
                    relocation_location = geolocator.geocode(location_params.get("relocation_location"))
                    if relocation_location:
                        relocation_lat, relocation_lon = relocation_location.latitude, relocation_location.longitude
                    else:
                        raise ValueError(f"Could not geocode relocation location: {location_params.get('relocation_location')}")
                
                # Create natal data at relocated location (as if born there)
                natal_data = Data(
                    name="Natal",
                    lat=relocation_lat,
                    lon=relocation_lon,
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Create transit data at relocated location
                transit_data_obj = Data(
                    name="Transit",
                    lat=relocation_lat,
                    lon=relocation_lon,
                    utc_dt=today_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Calculate stats between relocated natal and relocated transits
                stats = Stats(data1=natal_data, data2=transit_data_obj)
                
                # Initialize Zodiac service with relocated natal data
                from src.services.zodiac_service import Zodiac
                zodiac = Zodiac(natal_data)
                
                # Get zodiac signs from relocated natal data
                sun_sign = zodiac.get_sun_sign()
                moon_sign = zodiac.get_lunar_sign()
                ascendant_sign = zodiac.get_ascendant_sign()
                
                # Generate full report
                try:
                    full_report_markdown = stats.full_report(kind="markdown")
                    if isinstance(full_report_markdown, bytes):
                        full_report_markdown = full_report_markdown.decode('utf-8', errors='ignore')
                    full_report_markdown = full_report_markdown.encode('utf-8', errors='ignore').decode('utf-8')
                except Exception as e:
                    logger.warning(f"Failed to generate full report: {e}")
                    full_report_markdown = "Report generation failed due to encoding issues."
                
                # Create the transit_data dict
                transit_data = {
                    "full_report": full_report_markdown,
                    "sun_sign": sun_sign,
                    "moon_sign": moon_sign,
                    "rising_sign": ascendant_sign
                }
                
                logger.info(f"🔄 Generated relocation transit data keys: {list(transit_data.keys())}")
                logger.info(f"🔄 Sun sign: {transit_data.get('sun_sign')}")
                logger.info(f"🔄 Full report length: {len(transit_data.get('full_report', ''))}")
                
            except Exception as stats_error:
                logger.error(f"🔄 Error in relocation get_natal_stats: {str(stats_error)}")
                import traceback
                logger.error(f"🔄 Relocation traceback: {traceback.format_exc()}")
                raise stats_error
        else:
            raise ValueError(f"Unknown chart type: {chart_type}")
        
        # Cache the transit data
        cache_document = {
            "natal_id": mongo_id,
            "type": chart_type,
            "date": today_date,
            "chart_data": transit_data,
            "created_at": datetime.now()
        }
        
        # Add location parameters to cache if provided
        if location_params:
            cache_document["location_params"] = location_params
        
        logger.info(f"💾 Caching transit data for {mongo_id} type {chart_type} on {today_date}")
        insert_result = await natal_daily_collection.insert_one(cache_document)
        logger.info(f"💾 Cache insert result: {insert_result.inserted_id}")
        
        daily_record_id = str(insert_result.inserted_id)
        return {"chart_data": transit_data, "daily_record_id": daily_record_id}
        
    except Exception as e:
        logger.error(f"💥 Error getting/generating transit cache: {str(e)}")
        logger.error(f"💥 Exception type: {type(e)}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        # Return empty data on error
        return {
            "chart_data": {
                "full_report": f"Error generating {chart_type} transit data",
                "sun_sign": "unknown",
                "moon_sign": "unknown", 
                "rising_sign": "unknown"
            },
            "daily_record_id": None
        }


@app.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "message": "Prof. Warlock is running!",
        "status": "healthy",
        "version": APP_VERSION
    }








@app.post("/natal-chart")
async def create_natal_chart_record(
    request: NatalChartRequest,
    purchased: bool = Query(False, description="Premium access status"),
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Create a natal chart record in the database.
    
    Args:
        request: Birth information for natal chart
        purchased: Premium access status (true/false)
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Created record with MongoDB ID
    """
    try:
        # Create document in MongoDB
        document = {
            "first_name": request.first_name,
            "last_name": request.last_name,
            "birth_day": request.birth_day,
            "birth_month": request.birth_month,
            "birth_year": request.birth_year,
            "birth_time": request.birth_time,
            "birth_place": request.birth_place,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "timezone": request.timezone,
            "lang": request.lang or "en",
            "purchased": purchased,
            "created_at": datetime.now(),
            "status": "created",
            "s3_url": None,
            "s3_filename": None,
            "qr_url": None,
            "file_size": None
        }
        
        result = await natal_collection.insert_one(document)
        mongo_id = str(result.inserted_id)
        
        logger.info(f"💾 Created natal chart record with ID: {mongo_id}, purchased: {purchased}")

        # Generate QR code URL
        if request.lang and request.lang != "en":
            qr_url = f"https://goker.art/natal/{mongo_id}?lang={request.lang}"
        else:
            qr_url = f"https://goker.art/natal/{mongo_id}"

        # Update with QR URL
        await natal_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"qr_url": qr_url}}
        )

        return JSONResponse(content={
            "status": "success",
            "data": {
                "id": mongo_id,
                "purchased": purchased,
                "qr_url": qr_url,
                "user_info": {
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "birth_day": request.birth_day,
                    "birth_month": request.birth_month,
                    "birth_year": request.birth_year,
                    "birth_time": request.birth_time,
                    "birth_place": request.birth_place,
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "timezone": request.timezone,
                    "lang": request.lang
                },
                "created_at": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"💥 Error creating natal chart record: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create natal chart record: {str(e)}"
        )


@app.post("/natal-chart-image/{mongo_id}")
async def get_natal_chart_image(
    mongo_id: str,
    request: NatalTransitRequest,  # Using for birth validation
    api_key: str = Depends(verify_api_key)
) -> Response:
    """
    Get natal chart image by ID. Returns from S3 if available, otherwise generates and saves.
    
    Args:
        mongo_id: MongoDB document ID
        request: Birth information for validation
        api_key: API key for authentication
        
    Returns:
        Response: Natal chart image as PNG
    """
    try:
        # Validate birth information and get document
        birth_document = await validate_birth_info(
            mongo_id=mongo_id,
            birth_day=request.birth_day,
            birth_month=request.birth_month,
            birth_year=request.birth_year,
            birth_time=request.birth_time
        )
        
        # Check if image already exists in S3
        s3_url = birth_document.get("s3_url")
        s3_filename = birth_document.get("s3_filename")
        
        if s3_url and s3_filename:
            try:
                # Try to get image from S3
                logger.info(f"📥 Attempting to retrieve existing image from S3: {s3_filename}")
                s3_response = s3_client.get_object(Bucket=config.s3.BUCKET, Key=s3_filename)
                image_data = s3_response['Body'].read()
                
                logger.info(f"✅ Successfully retrieved image from S3 for {mongo_id}")
                
                # Return existing image
                return Response(
                    content=image_data,
                    media_type="image/png",
                    headers={
                        "Content-Type": "image/png",
                        "Content-Disposition": f'inline; filename="natal_chart_{birth_document.get("first_name", "chart")}.png"',
                        "X-Mongo-ID": mongo_id,
                        "X-S3-URL": s3_url,
                        "X-Source": "s3-cache"
                    }
                )
            except Exception as s3_error:
                logger.warning(f"⚠️ Could not retrieve from S3: {str(s3_error)}, will generate new image")

        # Generate new image if not found in S3
        logger.info(f"🎨 Generating new natal chart image for {mongo_id}")
        
        user_info = {
            "First Name": birth_document.get("first_name", ""),
            "Last Name": birth_document.get("last_name", ""),
            "Date of Birth": f"{birth_document['birth_day']:02d}-{birth_document['birth_month']:02d}-{birth_document['birth_year']} {birth_document['birth_time']}",
            "Place of Birth": birth_document.get("birth_place", ""),
            "Latitude": birth_document.get("latitude"),
            "Longitude": birth_document.get("longitude")
        }

        # Get QR URL from document
        qr_url = birth_document.get("qr_url")

        # Generate natal chart with QR code
        chart_data_bytes = natal_chart_service.generate_chart(
            user_info, 
            qr_url=qr_url, 
            template='5', 
            timezone=birth_document.get("timezone")
        )

        # Load image and save with 300 DPI
        image = Image.open(io.BytesIO(chart_data_bytes))
        
        # Save image to bytes with 300 DPI
        output = io.BytesIO()
        image.save(output, format='PNG', dpi=(300, 300))
        final_chart_data_bytes = output.getvalue()

        # Upload to S3
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_digest = sha256(final_chart_data_bytes).hexdigest()[:8]
        s3_filename = f"natal_charts/{timestamp}_{hash_digest}.png"

        s3_client.put_object(
            Bucket=config.s3.BUCKET,
            Key=s3_filename,
            Body=final_chart_data_bytes,
            ContentType='image/png'
        )

        # Generate S3 URL
        s3_url = f"{config.s3.PUBLIC_URL}{s3_filename}"

        # Update MongoDB document with S3 information
        update_document = {
            "s3_url": s3_url,
            "s3_filename": s3_filename,
            "file_size": len(final_chart_data_bytes),
            "status": "completed",
            "updated_at": datetime.now()
        }
        
        await natal_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": update_document}
        )
        
        logger.info(f"💾 Updated MongoDB document with new S3 URL: {mongo_id}")

        # Return the newly generated image
        return Response(
            content=final_chart_data_bytes,
            media_type="image/png",
            headers={
                "Content-Type": "image/png",
                "Content-Disposition": f'inline; filename="natal_chart_{birth_document.get("first_name", "chart")}.png"',
                "X-Mongo-ID": mongo_id,
                "X-S3-URL": s3_url,
                "X-QR-URL": qr_url,
                "X-Source": "generated"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error getting natal chart image: {str(e)}")
        # Mark document as failed if we have access to it
        try:
            await natal_collection.update_one(
                {"_id": ObjectId(mongo_id)},
                {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now()}}
            )
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal chart image: {str(e)}"
        )


@app.get("/natal-chart/{mongo_id}")
async def get_natal_chart_by_id(
    mongo_id: str,
    birth_date: str = Query(..., description="Birth date in format DD-MM-YYYY"),
    birth_time: str = Query(..., description="Birth time in format HH:MM"),
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Retrieve natal chart data by MongoDB ID and birth information.
    
    Args:
        mongo_id: MongoDB document ID
        birth_date: Birth date in DD-MM-YYYY format
        birth_time: Birth time in HH:MM format
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Natal chart data including S3 URL and stats
    """
    try:
        # Validate MongoDB ID format
        if not ObjectId.is_valid(mongo_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid MongoDB ID format"
            )
        
        # Parse birth date
        try:
            birth_day, birth_month, birth_year = birth_date.split('-')
            birth_day = int(birth_day)
            birth_month = int(birth_month)
            birth_year = int(birth_year)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid birth date format. Use DD-MM-YYYY"
            )
        
        # Query MongoDB with ID and birth information for security
        query = {
            "_id": ObjectId(mongo_id),
            "birth_day": birth_day,
            "birth_month": birth_month,
            "birth_year": birth_year,
            "birth_time": birth_time
        }
        
        document = await natal_collection.find_one(query)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail="Natal chart not found or birth information doesn't match"
            )
        
        # Convert ObjectId to string for JSON serialization
        document["_id"] = str(document["_id"])
        
        # Convert datetime fields to string if they exist
        for date_field in ["created_at", "updated_at"]:
            if date_field in document and document[date_field]:
                document[date_field] = document[date_field].isoformat()
        
        # Get or generate daily stats
        today_date = datetime.now().strftime("%Y-%m-%d")
        daily_stats = await get_or_generate_daily_stats(
            mongo_id=mongo_id,
            birth_day=document.get("birth_day"),
            birth_month=document.get("birth_month"),
            birth_year=document.get("birth_year"),
            birth_time=document.get("birth_time"),
            birth_place=document.get("birth_place"),
            latitude=document.get("latitude"),
            longitude=document.get("longitude"),
            timezone=document.get("timezone"),
            today_date=today_date
        )

        # Create response with organized data
        response_data = {
            "id": document["_id"],
            "user_info": {
                "first_name": document.get("first_name"),
                "last_name": document.get("last_name"),
                "birth_day": document.get("birth_day"),
                "birth_month": document.get("birth_month"),
                "birth_year": document.get("birth_year"),
                "birth_time": document.get("birth_time"),
                "birth_place": document.get("birth_place"),
                "latitude": document.get("latitude"),
                "longitude": document.get("longitude"),
                "timezone": document.get("timezone"),
                "lang": document.get("lang", "en")
            },
            "chart_info": {
                "s3_url": document.get("s3_url"),
                "qr_url": document.get("qr_url"),
                "file_size": document.get("file_size"),
                "status": document.get("status", "unknown")
            },
            "stats": daily_stats,
            "metadata": {
                "created_at": document.get("created_at"),
                "updated_at": document.get("updated_at")
            }
        }
        
        return JSONResponse(content={
            "status": "success",
            "data": response_data
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error retrieving natal chart: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve natal chart"
        )



@app.post("/natal-stats")
async def get_natal_stats(
    request: NatalStatsRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict:
    """
    Get natal stats including sun sign, moon sign, rising sign and transit information.
    
    Args:
        request: Birth information and optional today's date and time
        api_key: API key for authentication
        
    Returns:
        Dict: Natal stats and transit information
    """
    try:
        # Set default values for today's date and time if not provided
        today = datetime.now()
        today_day = request.today_day or today.day
        today_month = request.today_month or today.month
        today_year = request.today_year or today.year
        today_time = request.today_time or today.strftime("%H:%M")

        # Get natal stats with padded day and month
        stats = await natal_chart_service.get_natal_stats(
            birth_datetime=f"{request.birth_day:02d}-{request.birth_month:02d}-{request.birth_year} {request.birth_time}",
            birth_place=request.birth_place,
            latitude=request.latitude,
            longitude=request.longitude,
            today_date=f"{today_day:02d}-{today_month:02d}-{today_year}",
            today_time=today_time,
            timezone=request.timezone
        )
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get natal stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal stats: {str(e)}"
        )


@app.post("/natal-transit/{mongo_id}")
async def get_natal_transit(
    mongo_id: str,
    request: NatalTransitRequest,
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Get natal transit data (classic, free endpoint).
    
    Args:
        mongo_id: MongoDB document ID
        request: Birth information for validation
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Classic transit data with natal chart + current transits
    """
    try:
        # Validate birth information
        birth_document = await validate_birth_info(
            mongo_id=mongo_id,
            birth_day=request.birth_day,
            birth_month=request.birth_month,
            birth_year=request.birth_year,
            birth_time=request.birth_time
        )
        
        # Set default values for today if not provided
        today = datetime.now()
        today_day = request.today_day or today.day
        today_month = request.today_month or today.month
        today_year = request.today_year or today.year
        today_time = request.today_time or today.strftime("%H:%M")
        
        # Format dates for processing
        today_date = f"{today_year}-{today_month:02d}-{today_day:02d}"
        
        # Get or generate transit data from cache
        transit_result = await get_or_generate_transit_cache(
            mongo_id=mongo_id,
            chart_type="classic",
            birth_document=birth_document,
            today_date=today_date,
            today_time=today_time
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "chart_type": "classic",
                "mongo_id": mongo_id,
                "transit_date": today_date,
                "transit_time": today_time,
                "chart_data": transit_result["chart_data"],
                "daily_record_id": transit_result["daily_record_id"]
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error in natal transit endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal transit data: {str(e)}"
        )


@app.post("/natal-transit-location/{mongo_id}")
async def get_natal_transit_location(
    mongo_id: str,
    request: NatalTransitLocationRequest,
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Get natal transit location data (premium endpoint).
    
    Args:
        mongo_id: MongoDB document ID
        request: Birth information and current location for validation
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Location-based transit data with synastry effects
    """
    try:
        # Validate birth information
        birth_document = await validate_birth_info(
            mongo_id=mongo_id,
            birth_day=request.birth_day,
            birth_month=request.birth_month,
            birth_year=request.birth_year,
            birth_time=request.birth_time
        )
        
        # Check premium access
        await check_premium_access(birth_document)
        
        # Set default values for today if not provided
        today = datetime.now()
        today_day = request.today_day or today.day
        today_month = request.today_month or today.month
        today_year = request.today_year or today.year
        today_time = request.today_time or today.strftime("%H:%M")
        
        # Format dates for processing
        today_date = f"{today_year}-{today_month:02d}-{today_day:02d}"
        
        # Prepare location parameters
        location_params = {
            "current_location": request.current_location,
            "current_latitude": request.current_latitude,
            "current_longitude": request.current_longitude
        }
        
        # Get or generate transit data from cache
        transit_result = await get_or_generate_transit_cache(
            mongo_id=mongo_id,
            chart_type="location",
            birth_document=birth_document,
            today_date=today_date,
            today_time=today_time,
            location_params=location_params
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "chart_type": "location",
                "mongo_id": mongo_id,
                "transit_date": today_date,
                "transit_time": today_time,
                "current_location": request.current_location,
                "current_coordinates": {
                    "latitude": request.current_latitude,
                    "longitude": request.current_longitude
                },
                "chart_data": transit_result["chart_data"],
                "daily_record_id": transit_result["daily_record_id"]
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error in natal transit location endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal transit location data: {str(e)}"
        )


@app.post("/natal-transit-relocation/{mongo_id}")
async def get_natal_transit_relocation(
    mongo_id: str,
    request: NatalTransitRelocationRequest,
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Get natal transit relocation data (premium endpoint).
    
    Args:
        mongo_id: MongoDB document ID
        request: Birth information and relocation details
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Relocation-based transit data with relocated chart + transits
    """
    try:
        # Validate birth information
        birth_document = await validate_birth_info(
            mongo_id=mongo_id,
            birth_day=request.birth_day,
            birth_month=request.birth_month,
            birth_year=request.birth_year,
            birth_time=request.birth_time
        )
        
        # Check premium access
        await check_premium_access(birth_document)
        
        # Set default values for today if not provided
        today = datetime.now()
        today_day = request.today_day or today.day
        today_month = request.today_month or today.month
        today_year = request.today_year or today.year
        today_time = request.today_time or today.strftime("%H:%M")
        
        # Format dates for processing
        today_date = f"{today_year}-{today_month:02d}-{today_day:02d}"
        
        # Prepare location parameters
        location_params = {
            "relocation_location": request.relocation_location,
            "relocation_latitude": request.relocation_latitude,
            "relocation_longitude": request.relocation_longitude
        }
        
        # Get or generate transit data from cache
        transit_result = await get_or_generate_transit_cache(
            mongo_id=mongo_id,
            chart_type="relocation",
            birth_document=birth_document,
            today_date=today_date,
            today_time=today_time,
            location_params=location_params
        )
        
        return JSONResponse(content={
            "status": "success",
            "data": {
                "chart_type": "relocation",
                "mongo_id": mongo_id,
                "transit_date": today_date,
                "transit_time": today_time,
                "relocation_location": request.relocation_location,
                "relocation_coordinates": {
                    "latitude": request.relocation_latitude,
                    "longitude": request.relocation_longitude
                },
                "chart_data": transit_result["chart_data"],
                "daily_record_id": transit_result["daily_record_id"]
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error in natal transit relocation endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get natal transit relocation data: {str(e)}"
        )


@app.get("/natal-daily-image/{mongo_id}")
async def get_natal_daily_image(
    mongo_id: str,
    api_key: str = Depends(verify_api_key),
    if_none_match: Optional[str] = Header(None, alias="If-None-Match")
) -> Response:
    """
    Generate daily natal chart image from natal_daily collection record.
    
    Args:
        mongo_id: MongoDB natal_daily document ID or natal_id
        api_key: API key for authentication
        if_none_match: ETag header for cache validation
        
    Returns:
        Response: Generated natal chart image as PNG with caching headers
    """
    try:
        # Validate MongoDB ID format
        if not ObjectId.is_valid(mongo_id):
            raise HTTPException(
                status_code=400,
                detail="Invalid MongoDB ID format"
            )
        
        # Try to get natal_daily record first
        daily_record = await natal_daily_collection.find_one({"_id": ObjectId(mongo_id)})
        
        # If not found, try to find by natal_id (fallback for user convenience)
        if not daily_record:
            daily_record = await natal_daily_collection.find_one({"natal_id": mongo_id})
        
        if not daily_record:
            # Check if this is a natal record ID
            natal_record = await natal_collection.find_one({"_id": ObjectId(mongo_id)})
            if natal_record:
                raise HTTPException(
                    status_code=404,
                    detail=f"No daily chart records found for natal ID {mongo_id}. Use a natal_daily record ID instead."
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Daily natal chart record not found"
                )
        
        # Get related natal record for user info
        natal_record = await natal_collection.find_one({"_id": ObjectId(daily_record["natal_id"])})
        
        if not natal_record:
            raise HTTPException(
                status_code=404,
                detail="Related natal chart record not found"
            )
        
        # Generate ETag based on record data
        chart_type = daily_record.get("type") or "classic"  # Get type early for ETag
        etag_data = f"{mongo_id}_{daily_record['date']}_{chart_type}"
        if daily_record.get("location_params"):
            location_params = daily_record["location_params"]
            if "current_latitude" in location_params:
                etag_data += f"_{location_params['current_latitude']}_{location_params['current_longitude']}"
            elif "relocation_latitude" in location_params:
                etag_data += f"_{location_params['relocation_latitude']}_{location_params['relocation_longitude']}"
        
        etag = hashlib.md5(etag_data.encode()).hexdigest()
        
        # Check if client has cached version
        if if_none_match == etag:
            return Response(
                status_code=304,
                headers={
                    "ETag": etag,
                    "Cache-Control": "public, max-age=86400"
                }
            )
        
        # Prepare user info for chart generation
        user_info = {
            "First Name": natal_record.get("first_name", ""),
            "Last Name": natal_record.get("last_name", ""),
            "Date of Birth": f"{natal_record['birth_day']:02d}-{natal_record['birth_month']:02d}-{natal_record['birth_year']} {natal_record['birth_time']}",
            "Place of Birth": natal_record.get("birth_place", ""),
            "Latitude": natal_record.get("latitude"),
            "Longitude": natal_record.get("longitude")
        }
        
        # Get cached transit data (handle both chart_data and full_report fields)
        transit_data = daily_record.get("chart_data", {})
        location_params = daily_record.get("location_params", {})
        
        # Handle legacy records that may have full_report instead of chart_data
        if not transit_data and "full_report" in daily_record:
            logger.warning(f"Using full_report instead of chart_data for record {daily_record['_id']}")
            # For now, generate a basic chart without transit data
            transit_data = {}
        
        # Generate transit chart image based on chart type
        try:
            from natal.data import Data
            from natal.chart import Chart
            from natal.config import Config
            from datetime import datetime
            
            # Parse birth date and time
            birth_datetime = f"{natal_record['birth_day']:02d}-{natal_record['birth_month']:02d}-{natal_record['birth_year']} {natal_record['birth_time']}"
            birth_dt = datetime.strptime(birth_datetime, "%d-%m-%Y %H:%M")
            
            # Parse transit date and time (default to noon for daily charts)
            transit_date = daily_record["date"]  # YYYY-MM-DD format
            transit_time = "12:00"  # Default time for daily charts
            transit_dt = datetime.strptime(f"{transit_date} {transit_time}", "%Y-%m-%d %H:%M")
            
            # Convert to UTC if timezone is provided
            if natal_record.get("timezone"):
                from pytz import timezone
                tz = timezone(natal_record.get("timezone"))
                birth_utc_dt = tz.localize(birth_dt).astimezone(timezone('UTC')).replace(tzinfo=None)
                transit_utc_dt = tz.localize(transit_dt).astimezone(timezone('UTC')).replace(tzinfo=None)
            else:
                birth_utc_dt = birth_dt
                transit_utc_dt = transit_dt
            
            # Create Data objects based on chart type
            if chart_type == "classic":
                # Classic: both natal and transit at birth location
                natal_data = Data(
                    name="Natal",
                    lat=natal_record.get("latitude"),
                    lon=natal_record.get("longitude"),
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                transit_data = Data(
                    name="Transit",
                    lat=natal_record.get("latitude"),
                    lon=natal_record.get("longitude"),
                    utc_dt=transit_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
            elif chart_type == "location":
                # Location: natal at birth location, transit at current location
                natal_data = Data(
                    name="Natal",
                    lat=natal_record.get("latitude"),
                    lon=natal_record.get("longitude"),
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                # Use current location coordinates if available
                current_lat = location_params.get("current_latitude", natal_record.get("latitude"))
                current_lon = location_params.get("current_longitude", natal_record.get("longitude"))
                
                transit_data = Data(
                    name="Transit",
                    lat=current_lat,
                    lon=current_lon,
                    utc_dt=transit_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
            elif chart_type == "relocation":
                # Relocation: natal at relocated location, transit at relocated location
                relocation_lat = location_params.get("relocation_latitude", natal_record.get("latitude"))
                relocation_lon = location_params.get("relocation_longitude", natal_record.get("longitude"))
                
                natal_data = Data(
                    name="Natal",
                    lat=relocation_lat,
                    lon=relocation_lon,
                    utc_dt=birth_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
                transit_data = Data(
                    name="Transit",
                    lat=relocation_lat,
                    lon=relocation_lon,
                    utc_dt=transit_utc_dt.strftime("%Y-%m-%d %H:%M"),
                    config=Config()
                )
                
            else:
                raise ValueError(f"Unknown chart type: {chart_type}")
            
            # Create transit chart with both natal and transit data
            chart = Chart(data1=natal_data, data2=transit_data, width=1600)
            
            # Generate SVG chart
            chart_svg = chart.svg
            
            # Convert SVG to PNG
            import cairosvg
            chart_data_bytes = cairosvg.svg2png(
                bytestring=chart_svg.encode('utf-8'),
                output_width=1600,
                output_height=int(1600 * 1.414)  # A4 aspect ratio
            )
            
        except Exception as chart_error:
            logger.error(f"💥 Error generating transit chart: {str(chart_error)}")
            # Fallback to regular natal chart
            chart_data_bytes = natal_chart_service.generate_chart(
                user_info, 
                template='5', 
                timezone=natal_record.get("timezone")
            )
        
        # For transit charts, the image is already at the correct size
        # Only resize if it's a fallback chart from natal_chart_service
        if chart_type in ["classic", "location", "relocation"] and "chart_error" not in locals():
            # Transit chart is already generated at correct size
            final_image_bytes = chart_data_bytes
        else:
            # Load and resize image (fallback case)
            image = Image.open(io.BytesIO(chart_data_bytes))
            
            # Resize to 1600px width while maintaining aspect ratio
            target_width = 1600
            aspect_ratio = image.height / image.width
            target_height = int(target_width * aspect_ratio)
            
            resized_image = image.resize((target_width, target_height), Image.LANCZOS)
            
            # Save image to bytes
            output = io.BytesIO()
            resized_image.save(output, format='PNG')
            final_image_bytes = output.getvalue()
        
        # Generate filename for content disposition
        filename = f"natal_daily_{chart_type}_{natal_record.get('first_name', 'chart')}_{daily_record['date']}.png"
        
        # Return image with caching headers
        return Response(
            content=final_image_bytes,
            media_type="image/png",
            headers={
                "Content-Type": "image/png",
                "Content-Disposition": f'inline; filename="{filename}"',
                "ETag": etag,
                "Cache-Control": "public, max-age=86400",  # 24 hours
                "X-Chart-Type": chart_type,
                "X-Mongo-ID": mongo_id,
                "X-Natal-ID": daily_record["natal_id"],
                "X-Transit-Date": daily_record["date"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error generating natal daily image: {str(e)}")
        import traceback
        logger.error(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate natal daily image: {str(e)}"
        )






@app.get("/privacy")
async def privacy_policy(lang: str = Query("en", description="Language code (en=English, tr=Turkish)")):
    """Endpoint to provide information about data privacy in multiple languages."""
    
    # Validate language parameter
    if lang not in ["en", "tr"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid language parameter. Supported languages: en, tr"
        )
    
    privacy_texts = {
        "en": (
            "When you receive a natal chart poster from goker.art/natal, a record is created in the system "
            "and Astera AI securely processes the information (if any) by matching it with goker.art/natal services. "
            "No record is created for non-matching data."
        ),
        "tr": (
            "goker.art/natal tarafından sunulan natal chart posteri aldığınız zaman sisteme kaydınız oluşur ve "
            "Astera AI secure şekilde sizden aldığı bilgileri (eğer varsa) goker.art/natal servisleri ile "
            "eşleştirerek işler. Eşleşmeyen veriler için kayıt işlemi yapılmaz."
        )
    }
    
    return privacy_texts[lang]


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"💥 Unhandled exception: {str(exc)}")
    return JSONResponse(
        content={
            "status": "error",
            "message": "An unexpected error occurred",
            "detail": str(exc)
        },
        status_code=500
    ) 