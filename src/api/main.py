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
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from .. import __version__

from ..core.configuration import config
from ..core.domain_models import NatalChartRequest, NatalStatsRequest
from .webhook_handler import WebhookHandler
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
webhook_handler = WebhookHandler()
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
        # Create compound index for natal_daily collection for fast lookups
        await natal_daily_collection.create_index([("natal_id", 1), ("date", 1)], unique=True)
        logger.info("📇 Created indexes for natal_daily collection")
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    await create_indexes()


def verify_webhook_token(token: Optional[str] = Query(None)) -> str:
    """
    Verify webhook authentication token.
    
    Args:
        token: Token from query parameter
        
    Returns:
        str: Verified token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not token or token != config.security.WEBHOOK_SECRET_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing webhook token"
        )
    return token


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


@app.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "message": "Prof. Warlock is running!",
        "status": "healthy",
        "version": APP_VERSION
    }


@app.get("/health")
async def detailed_health_check():
    """Detailed health check with system information."""
    try:
        # Test MongoDB connection
        await mongodb_client.admin.command('ismaster')
        mongodb_status = "connected"
        
        # Get collection counts
        natal_count = await natal_collection.count_documents({})
        daily_count = await natal_daily_collection.count_documents({})
        
    except Exception as e:
        logger.error(f"MongoDB connection error: {str(e)}")
        mongodb_status = "disconnected"
        natal_count = 0
        daily_count = 0
    
    return {
        "status": "healthy",
        "service": "Prof. Warlock",
        "version": APP_VERSION,
        "features": [
            "email_parsing",
            "image_processing",
            "personalized_responses",
            "mongodb_storage",
            "daily_stats_caching"
        ],
        "database": {
            "mongodb": mongodb_status,
            "natal_charts": natal_count,
            "daily_stats": daily_count
        }
    }


@app.post("/webhook")
async def process_email_webhook(
    request: Request,
    token: str = Depends(verify_webhook_token)
):
    """
    Process incoming email webhooks from Postmark.
    
    Complete Email-to-AI-to-Email Workflow:
    1. Security validation (webhook token)
    2. Email parsing and cleaning
    3. PING/PONG health check handling
    4. Natal chart generation    
    5. Personalized email response
    
    Security: Requires valid token parameter for authentication.
    Usage: POST /webhook?token=your-secret-token
    """
    try:
        # Parse webhook data
        webhook_data = await request.json()
        logger.info(f"📧 Received webhook from: {webhook_data.get('From', 'unknown')}")
        
        # Process through webhook handler
        result = await webhook_handler.process_webhook(webhook_data)
        
        # Return appropriate response
        if result["status"] == "success":
            return JSONResponse(content=result, status_code=200)
        elif result["status"] == "partial_success":
            return JSONResponse(content=result, status_code=202)  # Accepted
        else:
            return JSONResponse(content=result, status_code=500)
            
    except Exception as e:
        logger.error(f"💥 Webhook endpoint error: {str(e)}")
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Webhook processing failed: {str(e)}"
            },
            status_code=500
        )


@app.post("/natal-chart")
async def generate_natal_chart(
    request: NatalChartRequest,
    api_key: str = Depends(verify_api_key)
) -> JSONResponse:
    """
    Generate a natal chart based on birth information.
    
    Args:
        request: Birth information for natal chart generation
        api_key: API key for authentication
        
    Returns:
        JSONResponse: Generated natal chart data and image
    """
    print('request', request)
    try:
        user_info = {
            "First Name": request.first_name,
            "Last Name": request.last_name,
            "Date of Birth": f"{request.birth_day:02d}-{request.birth_month:02d}-{request.birth_year} {request.birth_time}",
            "Place of Birth": request.birth_place,
            "Latitude": request.latitude,
            "Longitude": request.longitude
        }

        # Generate natal chart
        chart_data_bytes = natal_chart_service.generate_chart(user_info, timezone=request.timezone)

        # Resize image
        image = Image.open(io.BytesIO(chart_data_bytes))
        max_size = 1500
        image.thumbnail((max_size, max_size), Image.LANCZOS)

        # Save image to bytes
        output = io.BytesIO()
        image.save(output, format='PNG')
        resized_chart_data_bytes = output.getvalue()

        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_digest = sha256(resized_chart_data_bytes).hexdigest()[:8]
        filename = f"natal_charts/{timestamp}_{hash_digest}.png"

        # Upload to S3
        s3_client.put_object(
            Bucket=config.s3.BUCKET,
            Key=filename,
            Body=resized_chart_data_bytes,
            ContentType='image/png'
        )

        # Generate download link
        download_link = f"{config.s3.PUBLIC_URL}{filename}"

        return JSONResponse(content=[{
            "name": "natal_chart.png",
            "id": filename,
            "mime_type": "image/png",
            "download_link": download_link
        }])
    except Exception as e:
        return JSONResponse(content={
            "status": "error",
            "message": f"Failed to generate natal chart: {str(e)}"
        }, status_code=500)


@app.post("/natal-chart-image")
async def generate_natal_chart_image(
    request: NatalChartRequest,
    api_key: str = Depends(verify_api_key)
) -> Response:
    """
    Generate a natal chart image and return it directly.
    Also saves the chart to MongoDB with S3 URL and natal stats.
    
    Args:
        request: Birth information for natal chart generation
        api_key: API key for authentication
        
    Returns:
        Response: Generated natal chart image as PNG
    """
    try:
        # First, create a document in MongoDB to get the ID
        temp_document = {
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
            "created_at": datetime.now(),
            "status": "generating"
        }
        
        result = await natal_collection.insert_one(temp_document)
        mongo_id = str(result.inserted_id)
        
        logger.info(f"💾 Created temporary MongoDB document with ID: {mongo_id}")

        user_info = {
            "First Name": request.first_name,
            "Last Name": request.last_name,
            "Date of Birth": f"{request.birth_day:02d}-{request.birth_month:02d}-{request.birth_year} {request.birth_time}",
            "Place of Birth": request.birth_place,
            "Latitude": request.latitude,
            "Longitude": request.longitude
        }

        # Generate QR code URL with MongoDB ID and language parameter
        if request.lang and request.lang != "en":
            qr_url = f"https://goker.art/natal/{mongo_id}?lang={request.lang}"
        else:
            qr_url = f"https://goker.art/natal/{mongo_id}"

        # Generate natal chart with QR code
        chart_data_bytes = natal_chart_service.generate_chart(user_info, qr_url=qr_url, template='5', timezone=request.timezone)

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

        # Update MongoDB document with complete information (without stats)
        update_document = {
            "s3_url": s3_url,
            "s3_filename": s3_filename,
            "qr_url": qr_url,
            "file_size": len(final_chart_data_bytes),
            "status": "completed",
            "updated_at": datetime.now()
        }
        
        await natal_collection.update_one(
            {"_id": ObjectId(mongo_id)},
            {"$set": update_document}
        )
        
        logger.info(f"💾 Updated MongoDB document with S3 URL and stats: {mongo_id}")

        # Return the image directly
        return Response(
            content=final_chart_data_bytes,
            media_type="image/png",
            headers={
                "Content-Type": "image/png",
                "Content-Disposition": f'attachment; filename="natal_chart_{request.first_name}_{request.last_name}.png"',
                "X-Mongo-ID": mongo_id,
                "X-S3-URL": s3_url,
                "X-QR-URL": qr_url
            }
        )
    except Exception as e:
        logger.error(f"💥 Error generating natal chart image: {str(e)}")
        # If we have a mongo_id, mark the document as failed
        if 'mongo_id' in locals():
            try:
                await natal_collection.update_one(
                    {"_id": ObjectId(mongo_id)},
                    {"$set": {"status": "failed", "error": str(e), "updated_at": datetime.now()}}
                )
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail="Failed to generate natal chart image"
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


@app.get("/debug/mongodb")
async def debug_mongodb(api_key: str = Depends(verify_api_key)):
    """Debug endpoint to check MongoDB connection and collections."""
    try:
        # Test MongoDB connection
        admin_result = await mongodb_client.admin.command('ismaster')
        
        # Get collection counts
        natal_count = await natal_collection.count_documents({})
        daily_count = await natal_daily_collection.count_documents({})
        
        # Test insert and delete
        test_doc = {
            "natal_id": "test_id",
            "date": "2024-01-01",
            "created_at": datetime.now(),
            "test": True
        }
        
        insert_result = await natal_daily_collection.insert_one(test_doc)
        inserted_id = insert_result.inserted_id
        
        # Verify insertion
        found_doc = await natal_daily_collection.find_one({"_id": inserted_id})
        
        # Clean up test document
        delete_result = await natal_daily_collection.delete_one({"_id": inserted_id})
        
        return {
            "status": "success",
            "mongodb_connected": True,
            "admin_command": admin_result,
            "collections": {
                "natal": natal_count,
                "natal_daily": daily_count
            },
            "test_insert": {
                "inserted_id": str(inserted_id),
                "found_doc": found_doc is not None,
                "deleted_count": delete_result.deleted_count
            }
        }
        
    except Exception as e:
        logger.error(f"MongoDB debug error: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "mongodb_connected": False
        }


@app.get("/privacy")
async def privacy_policy():
    """Endpoint to provide information about data privacy."""
    return "This system does not store any data. It processes the provided information to generate insights and returns the results without retaining any data."


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