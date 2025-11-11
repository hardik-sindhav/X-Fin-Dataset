"""
Admin Panel for NSE FII/DII Data Collector
Web interface to monitor cronjob status and view data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from bson import ObjectId
from nse_fiidii_collector import NSEDataCollector
from nse_all_indices_option_chain_collector import NSEAllIndicesOptionChainCollector, INDICES
from scheduler_config import (
    get_all_config, get_config_for_scheduler, update_scheduler_config,
    get_holidays, add_holiday, remove_holiday, is_holiday
)
from nse_all_banks_option_chain_collector import NSEAllBanksOptionChainCollector, BANKS
from nse_all_gainers_losers_collector import NSEAllGainersLosersCollector
from nse_news_collector import NSENewsCollector
from nse_livemint_news_collector import NSELiveMintNewsCollector

# Twitter collector removed - not needed
import schedule
import json
import os
from datetime import datetime, timedelta, time as dt_time, timezone
from logger_config import setup_logging, get_logger, configure_flask_logging
import threading
import time as time_module
import psutil
import sys
import jwt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from urllib.parse import quote_plus
from validation_schemas import (
    LoginSchema, CombinedPaginationDateSchema, SchedulerConfigSchema,
    ConfigUpdateSchema, HolidaySchema
)
from validation_utils import (
    validate_json_body, validate_query_params, validate_path_param
)
from marshmallow import ValidationError

app = Flask(__name__)

# Setup centralized logging configuration
# Check if log file path is configured
log_file = os.getenv('LOG_FILE', None)
if log_file:
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else None
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

setup_logging(log_file=log_file)
configure_flask_logging(app)

# Get logger for this module
logger = get_logger(__name__)

# Security: Set maximum content length to prevent DoS attacks
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Security: Disable debug mode in production
if os.getenv('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Rate Limiting Configuration
# Use Redis if available, otherwise use in-memory storage
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Test Redis connection before using it
redis_available = False
if REDIS_HOST and REDIS_PORT:
    try:
        import redis
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            socket_connect_timeout=2,  # 2 second timeout
            socket_timeout=2
        )
        # Test connection
        redis_client.ping()
        redis_available = True
        logger.info(f"Redis connection successful at {REDIS_HOST}:{REDIS_PORT}")
        redis_client.close()
    except Exception as e:
        logger.warning(f"Redis not available for rate limiting: {str(e)}. Using in-memory storage.")
        redis_available = False

if redis_available:
    # Use Redis for rate limiting (better for production)
    try:
        if REDIS_PASSWORD:
            redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        else:
            redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            storage_uri=redis_url,
            default_limits=["200 per day", "50 per hour"],
            strategy="fixed-window",
            headers_enabled=True,
            swallow_errors=True  # Don't fail if Redis connection is lost during runtime
        )
        logger.debug("Rate limiting configured with Redis")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis limiter: {str(e)}. Falling back to in-memory storage.")
        redis_available = False

if not redis_available:
    # Fallback to in-memory storage if Redis is not available
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        strategy="fixed-window",
        headers_enabled=True
    )
    logger.debug("Rate limiting configured with in-memory storage (Redis not available)")

# Configure CORS to allow requests from frontend domain
# SECURITY: In production, CORS_ORIGINS must be set to restrict access
allowed_origins_env = os.getenv('CORS_ORIGINS', '')
flask_env = os.getenv('FLASK_ENV', 'production')

if allowed_origins_env:
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',')]
    CORS(app, 
         resources={r"/api/*": {
             "origins": allowed_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True
         }})
elif flask_env == 'production':
    # In production, if CORS_ORIGINS is not set, restrict to localhost only
    # This prevents accidental exposure while still allowing local access
    import warnings
    warnings.warn(
        "CORS_ORIGINS not set in production. Restricting to localhost only. "
        "Set CORS_ORIGINS environment variable to allow your frontend domain.",
        UserWarning
    )
    CORS(app, 
         resources={r"/api/*": {
             "origins": ["http://localhost:*", "https://localhost:*"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }})
else:
    # Development mode: allow all origins (not recommended for production)
    import warnings
    warnings.warn(
        "CORS is allowing all origins. This is only safe for development. "
        "Set CORS_ORIGINS environment variable for production.",
        UserWarning
    )
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"]
         }})

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', None)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '2'))  # Default 2 hours, was 24

# Validate JWT secret key on startup
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY environment variable is required. "
        "Generate a secure key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
if len(JWT_SECRET_KEY) < 32:
    raise ValueError(
        f"JWT_SECRET_KEY must be at least 32 characters long. "
        f"Current length: {len(JWT_SECRET_KEY)}"
    )

# Admin credentials loaded from environment variables
# Option 1: Set plain password in .env (recommended for simplicity)
# Option 2: Set password hash in .env (more secure, but requires generating hash)
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', None)  # Plain password from .env
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', None)  # Pre-hashed password from .env

# SECURITY: Require admin credentials to be explicitly configured
if not ADMIN_PASSWORD and not ADMIN_PASSWORD_HASH:
    raise ValueError(
        "Admin credentials must be configured. "
        "Set either ADMIN_PASSWORD or ADMIN_PASSWORD_HASH in your .env file. "
        "To generate a password hash: python -c \"from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))\""
    )

if ADMIN_PASSWORD:
    # If plain password is provided, hash it
    # Validate password strength
    if len(ADMIN_PASSWORD) < 8:
        raise ValueError("ADMIN_PASSWORD must be at least 8 characters long")
    ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)

STATUS_FILE = 'scheduler_status.json'
ALL_INDICES_STATUS_FILE = 'all_indices_option_chain_scheduler_status.json'
ALL_BANKS_STATUS_FILE = 'all_banks_option_chain_scheduler_status.json'
NEWS_COLLECTOR_STATUS_FILE = 'news_collector_scheduler_status.json'
LIVEMINT_NEWS_STATUS_FILE = 'livemint_news_scheduler_status.json'


def get_next_valid_date(start_date, max_days=30):
    """
    Get next valid date (weekday and not a holiday)
    start_date: date to start checking from
    max_days: maximum days to check ahead
    Returns: next valid date or None if not found
    """
    from datetime import date
    check_date = start_date
    for _ in range(max_days):
        # Check if it's a weekday (Monday=0 to Friday=4)
        if check_date.weekday() < 5:
            # Check if it's not a holiday
            if not is_holiday(check_date):
                return check_date
        check_date = check_date + timedelta(days=1)
    return None


def get_next_run_time():
    """Calculate next scheduled run time for FII/DII using config"""
    from scheduler_config import get_config_for_scheduler
    config = get_config_for_scheduler("fiidii")
    if not config or not config.get("enabled", True):
        return None
    
    now = datetime.now()
    current_time = now.time()
    start_time_str = config.get("start_time", "17:00")
    target_time = datetime.strptime(start_time_str, "%H:%M").time()
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # Check if today is a weekday and not a holiday
    if current_weekday < 5 and not is_holiday(now.date()):  # Monday to Friday, not holiday
        # If current time is before target time today, next run is today
        if current_time < target_time:
            next_run = datetime.combine(now.date(), target_time)
            return next_run
        else:
            # Today after target time, find next valid weekday
            next_date = get_next_valid_date(now.date() + timedelta(days=1))
            if next_date:
                next_run = datetime.combine(next_date, target_time)
                return next_run
    
    # Current day is weekend or holiday, find next valid date
    days_ahead = 1
    if current_weekday >= 5:  # Weekend
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        days_ahead = days_until_monday
    
    next_date = get_next_valid_date(now.date() + timedelta(days=days_ahead))
    if next_date:
        next_run = datetime.combine(next_date, target_time)
        return next_run
    
    return None


def check_scheduler_running(scheduler_file='cronjob_scheduler.py'):
    """Check if scheduler process is running"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and scheduler_file in ' '.join(cmdline):
                    return True, proc.info['pid']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False, None
    except Exception:
        return False, None


def get_pagination_params():
    """Get and validate pagination parameters from request"""
    page = request.args.get('page', default=1, type=int)
    limit = request.args.get('limit', default=15, type=int)
    
    # Ensure valid pagination values
    page = max(1, page)
    limit = max(1, min(100, limit))  # Limit between 1 and 100
    
    return page, limit


def get_scheduler_status():
    """Get scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running()
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            # If file exists but can't be read, status remains unknown
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


def safe_error_response(error: Exception, default_message: str = "An error occurred") -> tuple:
    """
    Create a safe error response that doesn't leak internal information.
    Logs full error details server-side, returns generic message to client.
    """
    logger = get_logger(__name__)
    
    # Log full error details server-side
    logger.error(f"Error: {type(error).__name__}: {str(error)}", exc_info=True)
    
    # Return generic error message to client (don't leak internal details)
    is_production = os.getenv('FLASK_ENV') == 'production'
    if is_production:
        return jsonify({
            "success": False,
            "error": default_message
        }), 500
    else:
        # In development, show more details
        return jsonify({
            "success": False,
            "error": str(error),
            "type": type(error).__name__
        }), 500


# ============================================================================
# GLOBAL ERROR HANDLERS
# ============================================================================

@app.errorhandler(400)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    app.logger.warning(f"Bad request: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": str(error) if not os.getenv('FLASK_ENV') == 'production' else "Invalid request parameters"
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    app.logger.warning(f"Unauthorized access attempt: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": "Authentication required"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    app.logger.warning(f"Forbidden access attempt: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Forbidden",
        "message": "You don't have permission to access this resource"
    }), 403


@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    app.logger.debug(f"Resource not found: {request.path}")
    return jsonify({
        "success": False,
        "error": "Not found",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    app.logger.warning(f"Method not allowed: {request.method} {request.path}")
    return jsonify({
        "success": False,
        "error": "Method not allowed",
        "message": f"The {request.method} method is not allowed for this endpoint"
    }), 405


@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle 413 Request Entity Too Large errors"""
    app.logger.warning(f"Request too large: {request.path}")
    return jsonify({
        "success": False,
        "error": "Request too large",
        "message": "The request payload is too large"
    }), 413


@app.errorhandler(429)
def too_many_requests(error):
    """Handle 429 Too Many Requests (rate limiting) errors"""
    app.logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.path}")
    return jsonify({
        "success": False,
        "error": "Too many requests",
        "message": "Rate limit exceeded. Please try again later."
    }), 429


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 Internal Server Error"""
    app.logger.error(f"Internal server error: {str(error)}", exc_info=True)
    
    is_production = os.getenv('FLASK_ENV') == 'production'
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred" if is_production else str(error)
    }), 500


@app.errorhandler(ValidationError)
def validation_error(error):
    """Handle Marshmallow validation errors"""
    app.logger.warning(f"Validation error: {error.messages}")
    return jsonify({
        "success": False,
        "error": "Validation failed",
        "errors": error.messages
    }), 400


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all unhandled exceptions"""
    app.logger.error(f"Unhandled exception: {type(error).__name__}: {str(error)}", exc_info=True)
    
    # If it's already a Flask error response, re-raise it
    if hasattr(error, 'code'):
        raise error
    
    is_production = os.getenv('FLASK_ENV') == 'production'
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred" if is_production else str(error),
        "type": type(error).__name__ if not is_production else None
    }), 500


def token_required(f):
    """Decorator to protect routes with JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
            except IndexError:
                return jsonify({'success': False, 'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        try:
            # Decode and verify token
            data = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            # You can add user info here if needed
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


@app.route("/")
@limiter.exempt  # Exempt health check from rate limiting
def home():
    """Root endpoint to check if API is running"""
    return jsonify({"status": "ok", "message": "API is running"})


@app.route('/api/mongodb/health', methods=['GET'])
@token_required
@limiter.limit("10 per minute")  # Health checks can be frequent but limit abuse
def api_mongodb_health():
    """API endpoint to check MongoDB connection status"""
    try:
        from pymongo import MongoClient
        
        # Get MongoDB configuration from environment variables
        MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
        MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
        MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
        MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
        MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)
        
        # Build MongoDB URI with URL-encoded credentials to handle special characters
        if MONGO_USERNAME and MONGO_PASSWORD:
            # URL-encode username and password to handle special characters like @, :, etc.
            encoded_username = quote_plus(MONGO_USERNAME)
            encoded_password = quote_plus(MONGO_PASSWORD)
            # Get auth source (default to 'admin' for MongoDB) - REQUIRED for authentication
            MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
            # Build connection string with authSource parameter (required for MongoDB auth)
            mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
        else:
            mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
        
        # Test connection
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        # Get database and check if it exists
        db = client[MONGO_DB_NAME]
        
        # Try to list collections to verify access
        collections = db.list_collection_names()
        
        # Get server info
        server_info = client.server_info()
        
        client.close()
        
        logger.debug(f"MongoDB health check successful: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME} ({len(collections)} collections)")
        
        return jsonify({
            "success": True,
            "connected": True,
            "host": MONGO_HOST,
            "port": MONGO_PORT,
            "database": MONGO_DB_NAME,
            "server_version": server_info.get('version', 'unknown'),
            "collections_count": len(collections),
            "message": "MongoDB connection successful"
        }), 200
        
    except Exception as e:
        # Don't expose MongoDB connection details in error
        is_production = os.getenv('FLASK_ENV') == 'production'
        error_msg = "MongoDB connection failed" if is_production else str(e)
        return jsonify({
            "success": False,
            "connected": False,
            "error": error_msg,
            "message": "MongoDB connection failed"
        }), 500


@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")  # Allow 5 login attempts per 15 minutes per IP
@validate_json_body(LoginSchema)
def api_login(validated_data):
    """API endpoint for user login - returns JWT token"""
    try:
        username = validated_data['username']
        password = validated_data['password']
        
        # Verify credentials
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            # Generate JWT token
            token_payload = {
                'username': username,
                'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
            }
            token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            logger.debug(f"Successful login: {username} from {request.remote_addr}")
            
            return jsonify({
                'success': True,
                'token': token,
                'username': username,
                'expires_in': JWT_EXPIRATION_HOURS * 3600  # seconds
            }), 200
        else:
            logger.warning(f"Failed login attempt: {username} from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
    
    except Exception as e:
        logger.error(f"Login error from {request.remote_addr}: {str(e)}", exc_info=True)
        return safe_error_response(e, "Login failed. Please try again.")


@app.route('/api/verify-token', methods=['GET'])
@token_required
def api_verify_token():
    """API endpoint to verify if token is valid"""
    return jsonify({
        'success': True,
        'message': 'Token is valid'
    }), 200


@app.route('/api/status')
@token_required
def api_status():
    """API endpoint to get scheduler status"""
    logger.debug(f"Scheduler status requested by {request.remote_addr}")
    status = get_scheduler_status()
    return jsonify(status)


@app.route('/api/data/<record_id>', methods=['DELETE'])
@token_required
@validate_path_param('record_id', ObjectId.is_valid, 'Invalid record ID')
def api_delete_data(record_id):
    """API endpoint to delete a specific FII/DII record"""
    try:
        collector = NSEDataCollector()
        
        # Delete the record
        result = collector.collection.delete_one({"_id": ObjectId(record_id)})
        
        collector.close()
        
        if result.deleted_count == 0:
            return jsonify({
                "success": False,
                "error": "Record not found"
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Record deleted successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/data')
@token_required
@validate_query_params(CombinedPaginationDateSchema)
def api_data(validated_data):
    """API endpoint to get collected data with pagination and date filtering"""
    try:
        collector = NSEDataCollector()
        
        # Get validated pagination parameters
        page = validated_data.get('page', 1)
        limit = validated_data.get('limit', 15)
        
        # Get validated date filter parameters (already validated as strings in YYYY-MM-DD format)
        start_date = validated_data.get('start_date')
        end_date = validated_data.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query_filter:
                query_filter["date"]["$lte"] = end_date
            else:
                query_filter["date"] = {"$lte": end_date}
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by date (newest first)
        records = list(collector.collection.find(query_filter).sort("date", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            record_dict = {
                "_id": str(record.get("_id")),
                "date": record.get("date"),
                "dii": record.get("dii", {}),
                "fii": record.get("fii", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats')
@token_required
def api_stats():
    """API endpoint to get statistics"""
    try:
        collector = NSEDataCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("date", -1)])
        
        stats = {
            "total_records": total_count,
            "latest_date": latest.get("date") if latest else None,
            "has_dii": bool(latest.get("dii", {})) if latest else False,
            "has_fii": bool(latest.get("fii", {})) if latest else False
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/trigger', methods=['POST'])
@token_required
def api_trigger():
    """API endpoint to manually trigger FII/DII data collection"""
    try:
        collector = NSEDataCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
        return jsonify({
            "success": success,
            "message": "Data collection completed" if success else "Data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Option Chain Endpoints

def get_interval_scheduler_next_run_time(scheduler_type):
    """
    Calculate next scheduled run time for interval-based schedulers using config
    scheduler_type: 'indices', 'banks', 'gainers_losers', 'gainers', 'losers', 'news'
    """
    from scheduler_config import get_config_for_scheduler
    config = get_config_for_scheduler(scheduler_type)
    if not config or not config.get("enabled", True):
        return None
    
    now = datetime.now()
    current_time = now.time()
    
    # Get config values
    start_time_str = config.get("start_time", "09:15")
    end_time_str = config.get("end_time", "15:30")
    interval_minutes = config.get("interval_minutes", 3)
    
    # Parse times
    start_time = datetime.strptime(start_time_str, "%H:%M").time()
    end_time = datetime.strptime(end_time_str, "%H:%M").time()
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # Check if today is a holiday
    today_is_holiday = is_holiday(now.date())
    
    # If it's a weekend or holiday, find next valid date
    if current_weekday >= 5 or today_is_holiday:  # Weekend or holiday
        days_until_valid = 1
        if current_weekday >= 5:  # Weekend
            days_until_monday = (7 - current_weekday) % 7
            if days_until_monday == 0:
                days_until_monday = 7
            days_until_valid = days_until_monday
        
        next_date = get_next_valid_date(now.date() + timedelta(days=days_until_valid))
        if next_date:
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return None
    
    # If before market opens today (and today is not a holiday), return today at start_time
    # But we need to double-check that today is not a holiday (in case it was just added)
    if current_time < start_time:
        if not is_holiday(now.date()):
            next_run = datetime.combine(now.date(), start_time)
            return next_run
        else:
            # Today is a holiday, find next valid date
            next_date = get_next_valid_date(now.date() + timedelta(days=1))
            if next_date:
                next_run = datetime.combine(next_date, start_time)
                return next_run
            return None
    
    # If after market closes today, return next valid date at start_time
    if current_time > end_time:
        next_date = get_next_valid_date(now.date() + timedelta(days=1))
        if next_date:
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return None
    
    # We're within market hours - calculate next interval
    start_datetime = datetime.combine(now.date(), start_time)
    minutes_from_start = int((now - start_datetime).total_seconds() / 60)
    
    # Calculate which interval we're in
    current_interval = minutes_from_start // interval_minutes
    
    # Calculate the next interval
    next_interval = current_interval + 1
    next_minutes_from_start = next_interval * interval_minutes
    
    # Calculate max minutes from start
    start_total_minutes = start_time.hour * 60 + start_time.minute
    end_total_minutes = end_time.hour * 60 + end_time.minute
    max_minutes_from_start = end_total_minutes - start_total_minutes
    
    if next_minutes_from_start > max_minutes_from_start:
        # Market closed, go to next valid date at start_time
        next_date = get_next_valid_date(now.date() + timedelta(days=1))
        if next_date:
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return None
    
    # Calculate next time
    next_total_minutes = start_total_minutes + next_minutes_from_start
    next_hour = next_total_minutes // 60
    next_minute = next_total_minutes % 60
    
    # Create the next run datetime on today's date
    next_run_date = now.date()
    next_run_time = dt_time(next_hour, next_minute)
    next_run = datetime.combine(next_run_date, next_run_time)
    
    # Double-check that the calculated date is not a holiday
    # (This handles cases where a holiday was added after the initial check)
    if is_holiday(next_run_date):
        # If the calculated time is on a holiday, find next valid date
        next_date = get_next_valid_date(next_run_date + timedelta(days=1))
        if next_date:
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return None
    
    return next_run


def get_option_chain_next_run_time():
    """Calculate next scheduled run time for option chain using config"""
    return get_interval_scheduler_next_run_time("indices")


def get_option_chain_status():
    """Get option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running (now using unified scheduler)
    is_running, pid = check_scheduler_running('all_indices_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_INDICES_STATUS_FILE):
        try:
            with open(ALL_INDICES_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract NIFTY specific result if available
                if "results" in file_status and "NIFTY" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["NIFTY"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/option-chain/status')
def api_option_chain_status():
    """API endpoint to get option chain scheduler status"""
    status = get_option_chain_status()
    return jsonify(status)


@app.route('/api/option-chain/expiry')
def api_option_chain_expiry():
    """API endpoint to get current NIFTY expiry date"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("NIFTY")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "NIFTY"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "NIFTY"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "NIFTY"
        }), 500


@app.route('/api/option-chain/data')
def api_option_chain_data():
    """API endpoint to get collected option chain data with pagination and date filtering"""
    try:
        collector, collection = get_index_collection("NIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for NIFTY"
            }), 404
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["records.timestamp"] = {"$gte": start_date}
        if end_date:
            if "records.timestamp" in query_filter:
                query_filter["records.timestamp"]["$lte"] = end_date
            else:
                query_filter["records.timestamp"] = {"$lte": end_date}
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            timestamp = record.get("records", {}).get("timestamp") if isinstance(record.get("records"), dict) else None
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": record.get("records", {}).get("underlyingValue") if isinstance(record.get("records"), dict) else None,
                "dataCount": len(record.get("records", {}).get("data", [])) if isinstance(record.get("records"), dict) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/option-chain/stats')
def api_option_chain_stats():
    """API endpoint to get option chain statistics"""
    try:
        collector, collection = get_index_collection("NIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for NIFTY"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("records.timestamp", -1)])
        
        latest_timestamp = None
        latest_underlying = None
        if latest and isinstance(latest.get("records"), dict):
            latest_timestamp = latest.get("records", {}).get("timestamp")
            latest_underlying = latest.get("records", {}).get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/option-chain/trigger', methods=['POST'])
def api_option_chain_trigger():
    """API endpoint to manually trigger option chain data collection"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        # Collect data for NIFTY only
        nifty_index = next((i for i in INDICES if i["symbol"] == "NIFTY"), None)
        if nifty_index:
            success = collector.collect_and_save_single_index(nifty_index)
        else:
            success = False
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "Option chain data collection completed" if success else "Option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/option-chain/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_option_chain_data_by_id(record_id):
    """API endpoint to get or delete a specific option chain record"""
    try:
        collector, collection = get_index_collection("NIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for NIFTY"
            }), 404
        
        # Validate ObjectId
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            # Delete the record
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# BankNifty Option Chain Endpoints

def get_banknifty_option_chain_next_run_time():
    """Calculate next scheduled run time for BankNifty option chain using config"""
    return get_interval_scheduler_next_run_time("indices")


def get_banknifty_option_chain_status():
    """Get BankNifty option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_indices_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_banknifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_INDICES_STATUS_FILE):
        try:
            with open(ALL_INDICES_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract BANKNIFTY specific result if available
                if "results" in file_status and "BANKNIFTY" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["BANKNIFTY"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/banknifty/status')
def api_banknifty_status():
    """API endpoint to get BankNifty option chain scheduler status"""
    status = get_banknifty_option_chain_status()
    return jsonify(status)


@app.route('/api/banknifty/data')
def api_banknifty_data():
    """API endpoint to get collected BankNifty option chain data with pagination and date filtering"""
    try:
        collector, collection = get_index_collection("BANKNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKNIFTY"
            }), 404
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["records.timestamp"] = {"$gte": start_date}
        if end_date:
            if "records.timestamp" in query_filter:
                query_filter["records.timestamp"]["$lte"] = end_date
            else:
                query_filter["records.timestamp"] = {"$lte": end_date}
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            timestamp = record.get("records", {}).get("timestamp") if isinstance(record.get("records"), dict) else None
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": record.get("records", {}).get("underlyingValue") if isinstance(record.get("records"), dict) else None,
                "dataCount": len(record.get("records", {}).get("data", [])) if isinstance(record.get("records"), dict) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/banknifty/expiry')
def api_banknifty_expiry():
    """API endpoint to get current BankNifty expiry date"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("BANKNIFTY")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "BANKNIFTY"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "BANKNIFTY"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "BANKNIFTY"
        }), 500


@app.route('/api/banknifty/stats')
def api_banknifty_stats():
    """API endpoint to get BankNifty option chain statistics"""
    try:
        collector, collection = get_index_collection("BANKNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKNIFTY"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("records.timestamp", -1)])
        
        latest_timestamp = None
        latest_underlying = None
        if latest and isinstance(latest.get("records"), dict):
            latest_timestamp = latest.get("records", {}).get("timestamp")
            latest_underlying = latest.get("records", {}).get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/banknifty/trigger', methods=['POST'])
def api_banknifty_trigger():
    """API endpoint to manually trigger BankNifty option chain data collection"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        # Collect data for BANKNIFTY only
        banknifty_index = next((i for i in INDICES if i["symbol"] == "BANKNIFTY"), None)
        if banknifty_index:
            success = collector.collect_and_save_single_index(banknifty_index)
        else:
            success = False
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "BankNifty option chain data collection completed" if success else "BankNifty option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/banknifty/data/<record_id>', methods=['GET'])
@token_required
def api_get_banknifty_data(record_id):
    """API endpoint to get a specific BankNifty option chain record with full data"""
    try:
        collector, collection = get_index_collection("BANKNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKNIFTY"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/banknifty/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_banknifty_data(record_id):
    """API endpoint to delete a specific BankNifty option chain record"""
    try:
        collector, collection = get_index_collection("BANKNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKNIFTY"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Finnifty Option Chain Endpoints

def get_finnifty_option_chain_next_run_time():
    """Calculate next scheduled run time for Finnifty option chain using config"""
    return get_interval_scheduler_next_run_time("indices")


def get_finnifty_option_chain_status():
    """Get Finnifty option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_indices_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_finnifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_INDICES_STATUS_FILE):
        try:
            with open(ALL_INDICES_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract FINNIFTY specific result if available
                if "results" in file_status and "FINNIFTY" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["FINNIFTY"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/finnifty/status')
def api_finnifty_status():
    """API endpoint to get Finnifty option chain scheduler status"""
    status = get_finnifty_option_chain_status()
    return jsonify(status)


@app.route('/api/finnifty/data')
@token_required
def api_finnifty_data():
    """API endpoint to get collected Finnifty option chain data with pagination and date filtering"""
    try:
        collector, collection = get_index_collection("FINNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FINNIFTY"
            }), 404
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["records.timestamp"] = {"$gte": start_date}
        if end_date:
            if "records.timestamp" in query_filter:
                query_filter["records.timestamp"]["$lte"] = end_date
            else:
                query_filter["records.timestamp"] = {"$lte": end_date}
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            timestamp = record.get("records", {}).get("timestamp") if isinstance(record.get("records"), dict) else None
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": record.get("records", {}).get("underlyingValue") if isinstance(record.get("records"), dict) else None,
                "dataCount": len(record.get("records", {}).get("data", [])) if isinstance(record.get("records"), dict) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit  # Ceiling division
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/finnifty/expiry')
def api_finnifty_expiry():
    """API endpoint to get current Finnifty expiry date"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("FINNIFTY")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "FINNIFTY"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "FINNIFTY"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "FINNIFTY"
        }), 500


@app.route('/api/finnifty/stats')
def api_finnifty_stats():
    """API endpoint to get Finnifty option chain statistics"""
    try:
        collector, collection = get_index_collection("FINNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FINNIFTY"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("records.timestamp", -1)])
        
        latest_timestamp = None
        latest_underlying = None
        if latest and isinstance(latest.get("records"), dict):
            latest_timestamp = latest.get("records", {}).get("timestamp")
            latest_underlying = latest.get("records", {}).get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/finnifty/trigger', methods=['POST'])
def api_finnifty_trigger():
    """API endpoint to manually trigger Finnifty option chain data collection"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        # Collect data for FINNIFTY only
        finnifty_index = next((i for i in INDICES if i["symbol"] == "FINNIFTY"), None)
        if finnifty_index:
            success = collector.collect_and_save_single_index(finnifty_index)
        else:
            success = False
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "Finnifty option chain data collection completed" if success else "Finnifty option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/finnifty/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_finnifty_data_by_id(record_id):
    """API endpoint to get or delete a specific Finnifty option chain record"""
    try:
        collector, collection = get_index_collection("FINNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FINNIFTY"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# MidcapNifty Option Chain Endpoints

def get_midcpnifty_option_chain_next_run_time():
    """Calculate next scheduled run time for MidcapNifty option chain using config"""
    return get_interval_scheduler_next_run_time("indices")


def get_midcpnifty_option_chain_status():
    """Get MidcapNifty option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_indices_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_midcpnifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_INDICES_STATUS_FILE):
        try:
            with open(ALL_INDICES_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract MIDCPNIFTY specific result if available
                if "results" in file_status and "MIDCPNIFTY" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["MIDCPNIFTY"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/midcpnifty/status')
def api_midcpnifty_status():
    """API endpoint to get MidcapNifty option chain scheduler status"""
    status = get_midcpnifty_option_chain_status()
    return jsonify(status)


@app.route('/api/midcpnifty/data')
@token_required
def api_midcpnifty_data():
    """API endpoint to get collected MidcapNifty option chain data with pagination and date filtering"""
    try:
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["records.timestamp"] = {"$gte": start_date}
        if end_date:
            if "records.timestamp" in query_filter:
                query_filter["records.timestamp"]["$lte"] = end_date
            else:
                query_filter["records.timestamp"] = {"$lte": end_date}
        
        skip = (page - 1) * limit
        
        collector, collection = get_index_collection("MIDCPNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for MIDCPNIFTY"
            }), 404
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            if isinstance(records_data, dict):
                timestamp = records_data.get("timestamp")
                underlying_value = records_data.get("underlyingValue")
                data_array = records_data.get("data", [])
            else:
                timestamp = None
                underlying_value = None
                data_array = []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/midcpnifty/expiry')
def api_midcpnifty_expiry():
    """API endpoint to get current MidcapNifty expiry date"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("MIDCPNIFTY")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "MIDCPNIFTY"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "MIDCPNIFTY"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "MIDCPNIFTY"
        }), 500


@app.route('/api/midcpnifty/stats')
def api_midcpnifty_stats():
    """API endpoint to get MidcapNifty option chain statistics"""
    try:
        collector, collection = get_index_collection("MIDCPNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for MIDCPNIFTY"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("records.timestamp", -1)])
        
        latest_timestamp = None
        latest_underlying = None
        if latest:
            records_data = latest.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/midcpnifty/trigger', methods=['POST'])
def api_midcpnifty_trigger():
    """API endpoint to manually trigger MidcapNifty option chain data collection"""
    try:
        collector = NSEAllIndicesOptionChainCollector()
        # Collect data for MIDCPNIFTY only
        midcpnifty_index = next((i for i in INDICES if i["symbol"] == "MIDCPNIFTY"), None)
        if midcpnifty_index:
            success = collector.collect_and_save_single_index(midcpnifty_index)
        else:
            success = False
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "MidcapNifty option chain data collection completed" if success else "MidcapNifty option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/midcpnifty/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_midcpnifty_data_by_id(record_id):
    """API endpoint to get or delete a specific MidcapNifty option chain record"""
    try:
        collector, collection = get_index_collection("MIDCPNIFTY")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for MIDCPNIFTY"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# HDFC Bank Option Chain Endpoints

def get_all_banks_option_chain_next_run_time():
    """Calculate next scheduled run time for All Banks option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_all_banks_option_chain_status():
    """Get All Banks option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_all_banks_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
                # Include bank-level results if available
                if "results" in file_status:
                    status["bank_results"] = file_status.get("results", {})
                    status["successful"] = file_status.get("successful", 0)
                    status["failed"] = file_status.get("failed", 0)
                    status["total"] = file_status.get("total", len(BANKS))
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/all-banks/status')
def api_all_banks_status():
    """API endpoint to get All Banks option chain scheduler status"""
    status = get_all_banks_option_chain_status()
    return jsonify(status)


# Helper function to get collection for a specific bank
def get_bank_collection(symbol: str):
    """Get MongoDB collection for a specific bank symbol"""
    collector = NSEAllBanksOptionChainCollector()
    collection = collector.get_collection(symbol)
    return collector, collection


# Helper function to get collection for a specific index
def get_index_collection(symbol: str):
    """Get MongoDB collection for a specific index symbol"""
    collector = NSEAllIndicesOptionChainCollector()
    collection = collector.get_collection(symbol)
    return collector, collection


# Helper function to get collection for gainers or losers
def get_gainers_collection():
    """Get MongoDB collection for gainers"""
    collector = NSEAllGainersLosersCollector()
    collection = collector.get_collection("gainers")
    return collector, collection

def get_losers_collection():
    """Get MongoDB collection for losers"""
    collector = NSEAllGainersLosersCollector()
    collection = collector.get_collection("losers")
    return collector, collection


# Helper function to get bank symbol from endpoint path
def get_bank_symbol_from_path(path: str) -> str:
    """Extract bank symbol from API path (e.g., /api/hdfcbank/data -> HDFCBANK)"""
    bank_mappings = {
        'hdfcbank': 'HDFCBANK',
        'icicibank': 'ICICIBANK',
        'sbin': 'SBIN',
        'kotakbank': 'KOTAKBANK',
        'axisbank': 'AXISBANK',
        'bankbaroda': 'BANKBARODA',
        'pnb': 'PNB',
        'canbk': 'CANBK',
        'aubank': 'AUBANK',
        'indusindbk': 'INDUSINDBK',
        'idfcfirstb': 'IDFCFIRSTB',
        'federalbnk': 'FEDERALBNK'
    }
    for key, symbol in bank_mappings.items():
        if key in path.lower():
            return symbol
    return None


@app.route('/api/hdfcbank/status')
def api_hdfcbank_status():
    """API endpoint to get HDFC Bank option chain scheduler status (deprecated - use /api/all-banks/status)"""
    # Return status from unified scheduler
    status = get_all_banks_option_chain_status()
    # Extract HDFCBANK specific result if available
    if "bank_results" in status and "HDFCBANK" in status["bank_results"]:
        status["last_status"] = "success" if status["bank_results"]["HDFCBANK"] else "failed"
    return jsonify(status)


@app.route('/api/hdfcbank/data')
@token_required
def api_hdfcbank_data():
    """API endpoint to get collected HDFC Bank option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("HDFCBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for HDFCBANK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/hdfcbank/expiry')
def api_hdfcbank_expiry():
    """API endpoint to get current HDFC Bank expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        # Get expiry for HDFCBANK
        expiry = collector._fetch_expiry_dates_with_retry("HDFCBANK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "HDFCBANK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "HDFCBANK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "HDFCBANK"
        }), 500


@app.route('/api/hdfcbank/stats')
def api_hdfcbank_stats():
    """API endpoint to get HDFC Bank option chain statistics"""
    try:
        collector, collection = get_bank_collection("HDFCBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for HDFCBANK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/hdfcbank/trigger', methods=['POST'])
def api_hdfcbank_trigger():
    """API endpoint to manually trigger HDFC Bank option chain data collection"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        # Collect data for HDFCBANK only
        hdfc_bank = next((b for b in BANKS if b["symbol"] == "HDFCBANK"), None)
        if hdfc_bank:
            success = collector.collect_and_save_single_bank(hdfc_bank)
        else:
            success = False
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "HDFC Bank option chain data collection completed" if success else "HDFC Bank option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/hdfcbank/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_hdfcbank_data_by_id(record_id):
    """API endpoint to get or delete a specific HDFC Bank option chain record"""
    try:
        collector, collection = get_bank_collection("HDFCBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for HDFCBANK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ICICI Bank Option Chain Endpoints

def get_icicibank_option_chain_next_run_time():
    """Calculate next scheduled run time for ICICI Bank option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_icicibank_option_chain_status():
    """Get ICICI Bank option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running (now using unified scheduler)
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_icicibank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract ICICIBANK specific result if available
                if "results" in file_status and "ICICIBANK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["ICICIBANK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/icicibank/status')
def api_icicibank_status():
    """API endpoint to get ICICI Bank option chain scheduler status"""
    status = get_icicibank_option_chain_status()
    return jsonify(status)


@app.route('/api/icicibank/data')
@token_required
def api_icicibank_data():
    """API endpoint to get collected ICICI Bank option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("ICICIBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for ICICIBANK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/icicibank/expiry')
def api_icicibank_expiry():
    """API endpoint to get current ICICI Bank expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("ICICIBANK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "ICICIBANK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "ICICIBANK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "ICICIBANK"
        }), 500


@app.route('/api/icicibank/stats')
def api_icicibank_stats():
    """API endpoint to get ICICI Bank option chain statistics"""
    try:
        collector, collection = get_bank_collection("ICICIBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for ICICIBANK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/icicibank/trigger', methods=['POST'])
def api_icicibank_trigger():
    """API endpoint to manually trigger ICICI Bank option chain data collection"""
    try:
        collector, collection = get_bank_collection("ICICIBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for ICICIBANK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "ICICI Bank option chain data collection completed" if success else "ICICI Bank option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/icicibank/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_icicibank_data_by_id(record_id):
    """API endpoint to get or delete a specific ICICI Bank option chain record"""
    try:
        collector, collection = get_bank_collection("ICICIBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for ICICIBANK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# SBIN Option Chain Endpoints

def get_sbin_option_chain_next_run_time():
    """Calculate next scheduled run time for SBIN option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_sbin_option_chain_status():
    """Get SBIN option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_sbin_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract SBIN specific result if available
                if "results" in file_status and "SBIN" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["SBIN"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/sbin/status')
def api_sbin_status():
    """API endpoint to get SBIN option chain scheduler status"""
    status = get_sbin_option_chain_status()
    return jsonify(status)


@app.route('/api/sbin/data')
@token_required
def api_sbin_data():
    """API endpoint to get collected SBIN option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("SBIN")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for SBIN"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sbin/expiry')
def api_sbin_expiry():
    """API endpoint to get current SBIN expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("SBIN")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "SBIN"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "SBIN"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "SBIN"
        }), 500


@app.route('/api/sbin/stats')
def api_sbin_stats():
    """API endpoint to get SBIN option chain statistics"""
    try:
        collector, collection = get_bank_collection("SBIN")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for SBIN"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sbin/trigger', methods=['POST'])
def api_sbin_trigger():
    """API endpoint to manually trigger SBIN option chain data collection"""
    try:
        collector, collection = get_bank_collection("SBIN")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for SBIN"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "SBIN option chain data collection completed" if success else "SBIN option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sbin/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_sbin_data_by_id(record_id):
    """API endpoint to get or delete a specific SBIN option chain record"""
    try:
        collector, collection = get_bank_collection("SBIN")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for SBIN"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Kotak Bank Option Chain Endpoints

def get_kotakbank_option_chain_next_run_time():
    """Calculate next scheduled run time for Kotak Bank option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_kotakbank_option_chain_status():
    """Get Kotak Bank option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_kotakbank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract KOTAKBANK specific result if available
                if "results" in file_status and "KOTAKBANK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["KOTAKBANK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/kotakbank/status')
def api_kotakbank_status():
    """API endpoint to get Kotak Bank option chain scheduler status"""
    status = get_kotakbank_option_chain_status()
    return jsonify(status)


@app.route('/api/kotakbank/data')
@token_required
def api_kotakbank_data():
    """API endpoint to get collected Kotak Bank option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("KOTAKBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for KOTAKBANK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/kotakbank/expiry')
def api_kotakbank_expiry():
    """API endpoint to get current Kotak Bank expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("KOTAKBANK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "KOTAKBANK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "KOTAKBANK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "KOTAKBANK"
        }), 500


@app.route('/api/kotakbank/stats')
def api_kotakbank_stats():
    """API endpoint to get Kotak Bank option chain statistics"""
    try:
        collector, collection = get_bank_collection("KOTAKBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for KOTAKBANK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/kotakbank/trigger', methods=['POST'])
def api_kotakbank_trigger():
    """API endpoint to manually trigger Kotak Bank option chain data collection"""
    try:
        collector, collection = get_bank_collection("KOTAKBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for KOTAKBANK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "Kotak Bank option chain data collection completed" if success else "Kotak Bank option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/kotakbank/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_kotakbank_data_by_id(record_id):
    """API endpoint to get or delete a specific Kotak Bank option chain record"""
    try:
        collector, collection = get_bank_collection("KOTAKBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for KOTAKBANK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Axis Bank Option Chain Endpoints

def get_axisbank_option_chain_next_run_time():
    """Calculate next scheduled run time for Axis Bank option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_axisbank_option_chain_status():
    """Get Axis Bank option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_axisbank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract AXISBANK specific result if available
                if "results" in file_status and "AXISBANK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["AXISBANK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/axisbank/status')
def api_axisbank_status():
    """API endpoint to get Axis Bank option chain scheduler status"""
    status = get_axisbank_option_chain_status()
    return jsonify(status)


@app.route('/api/axisbank/data')
@token_required
def api_axisbank_data():
    """API endpoint to get collected Axis Bank option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("AXISBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AXISBANK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/axisbank/expiry')
def api_axisbank_expiry():
    """API endpoint to get current Axis Bank expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("AXISBANK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "AXISBANK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "AXISBANK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "AXISBANK"
        }), 500


@app.route('/api/axisbank/stats')
def api_axisbank_stats():
    """API endpoint to get Axis Bank option chain statistics"""
    try:
        collector, collection = get_bank_collection("AXISBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AXISBANK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/axisbank/trigger', methods=['POST'])
def api_axisbank_trigger():
    """API endpoint to manually trigger Axis Bank option chain data collection"""
    try:
        collector, collection = get_bank_collection("AXISBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AXISBANK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "Axis Bank option chain data collection completed" if success else "Axis Bank option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/axisbank/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_axisbank_data_by_id(record_id):
    """API endpoint to get or delete a specific Axis Bank option chain record"""
    try:
        collector, collection = get_bank_collection("AXISBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AXISBANK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Bank of Baroda Option Chain Endpoints

def get_bankbaroda_option_chain_next_run_time():
    """Calculate next scheduled run time for Bank of Baroda option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_bankbaroda_option_chain_status():
    """Get Bank of Baroda option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_bankbaroda_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract BANKBARODA specific result if available
                if "results" in file_status and "BANKBARODA" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["BANKBARODA"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/bankbaroda/status')
def api_bankbaroda_status():
    """API endpoint to get Bank of Baroda option chain scheduler status"""
    status = get_bankbaroda_option_chain_status()
    return jsonify(status)


@app.route('/api/bankbaroda/data')
@token_required
def api_bankbaroda_data():
    """API endpoint to get collected Bank of Baroda option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("BANKBARODA")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKBARODA"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/bankbaroda/expiry')
def api_bankbaroda_expiry():
    """API endpoint to get current Bank of Baroda expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("BANKBARODA")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "BANKBARODA"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "BANKBARODA"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "BANKBARODA"
        }), 500


@app.route('/api/bankbaroda/stats')
def api_bankbaroda_stats():
    """API endpoint to get Bank of Baroda option chain statistics"""
    try:
        collector, collection = get_bank_collection("BANKBARODA")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKBARODA"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/bankbaroda/trigger', methods=['POST'])
def api_bankbaroda_trigger():
    """API endpoint to manually trigger Bank of Baroda option chain data collection"""
    try:
        collector, collection = get_bank_collection("BANKBARODA")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKBARODA"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "Bank of Baroda option chain data collection completed" if success else "Bank of Baroda option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/bankbaroda/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_bankbaroda_data_by_id(record_id):
    """API endpoint to get or delete a specific Bank of Baroda option chain record"""
    try:
        collector, collection = get_bank_collection("BANKBARODA")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for BANKBARODA"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# PNB Option Chain Endpoints

def get_pnb_option_chain_next_run_time():
    """Calculate next scheduled run time for PNB option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_pnb_option_chain_status():
    """Get PNB option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_pnb_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract PNB specific result if available
                if "results" in file_status and "PNB" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["PNB"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/pnb/status')
def api_pnb_status():
    """API endpoint to get PNB option chain scheduler status"""
    status = get_pnb_option_chain_status()
    return jsonify(status)


@app.route('/api/pnb/data')
@token_required
def api_pnb_data():
    """API endpoint to get collected PNB option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("PNB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for PNB"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pnb/expiry')
def api_pnb_expiry():
    """API endpoint to get current PNB expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("PNB")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "PNB"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "PNB"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "PNB"
        }), 500


@app.route('/api/pnb/stats')
def api_pnb_stats():
    """API endpoint to get PNB option chain statistics"""
    try:
        collector, collection = get_bank_collection("PNB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for PNB"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pnb/trigger', methods=['POST'])
def api_pnb_trigger():
    """API endpoint to manually trigger PNB option chain data collection"""
    try:
        collector, collection = get_bank_collection("PNB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for PNB"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "PNB option chain data collection completed" if success else "PNB option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/pnb/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_pnb_data_by_id(record_id):
    """API endpoint to get or delete a specific PNB option chain record"""
    try:
        collector, collection = get_bank_collection("PNB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for PNB"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# CANBK Option Chain Endpoints

def get_canbk_option_chain_next_run_time():
    """Calculate next scheduled run time for CANBK option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_canbk_option_chain_status():
    """Get CANBK option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_canbk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract CANBK specific result if available
                if "results" in file_status and "CANBK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["CANBK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/canbk/status')
def api_canbk_status():
    """API endpoint to get CANBK option chain scheduler status"""
    status = get_canbk_option_chain_status()
    return jsonify(status)


@app.route('/api/canbk/data')
@token_required
def api_canbk_data():
    """API endpoint to get collected CANBK option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("CANBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for CANBK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/canbk/expiry')
def api_canbk_expiry():
    """API endpoint to get current CANBK expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("CANBK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "CANBK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "CANBK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "CANBK"
        }), 500


@app.route('/api/canbk/stats')
def api_canbk_stats():
    """API endpoint to get CANBK option chain statistics"""
    try:
        collector, collection = get_bank_collection("CANBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for CANBK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/canbk/trigger', methods=['POST'])
def api_canbk_trigger():
    """API endpoint to manually trigger CANBK option chain data collection"""
    try:
        collector, collection = get_bank_collection("CANBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for CANBK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "CANBK option chain data collection completed" if success else "CANBK option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/canbk/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_canbk_data_by_id(record_id):
    """API endpoint to get or delete a specific CANBK option chain record"""
    try:
        collector, collection = get_bank_collection("CANBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for CANBK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# AUBANK Option Chain Endpoints

def get_aubank_option_chain_next_run_time():
    """Calculate next scheduled run time for AUBANK option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_aubank_option_chain_status():
    """Get AUBANK option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_aubank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract AUBANK specific result if available
                if "results" in file_status and "AUBANK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["AUBANK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/aubank/status')
def api_aubank_status():
    """API endpoint to get AUBANK option chain scheduler status"""
    status = get_aubank_option_chain_status()
    return jsonify(status)


@app.route('/api/aubank/data')
@token_required
def api_aubank_data():
    """API endpoint to get collected AUBANK option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("AUBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AUBANK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/aubank/expiry')
def api_aubank_expiry():
    """API endpoint to get current AUBANK expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("AUBANK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "AUBANK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "AUBANK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "AUBANK"
        }), 500


@app.route('/api/aubank/stats')
def api_aubank_stats():
    """API endpoint to get AUBANK option chain statistics"""
    try:
        collector, collection = get_bank_collection("AUBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AUBANK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/aubank/trigger', methods=['POST'])
def api_aubank_trigger():
    """API endpoint to manually trigger AUBANK option chain data collection"""
    try:
        collector, collection = get_bank_collection("AUBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AUBANK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "AUBANK option chain data collection completed" if success else "AUBANK option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/aubank/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_aubank_data_by_id(record_id):
    """API endpoint to get or delete a specific AUBANK option chain record"""
    try:
        collector, collection = get_bank_collection("AUBANK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for AUBANK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# INDUSINDBK Option Chain Endpoints

def get_indusindbk_option_chain_next_run_time():
    """Calculate next scheduled run time for INDUSINDBK option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_indusindbk_option_chain_status():
    """Get INDUSINDBK option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_indusindbk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract INDUSINDBK specific result if available
                if "results" in file_status and "INDUSINDBK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["INDUSINDBK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/indusindbk/status')
def api_indusindbk_status():
    """API endpoint to get INDUSINDBK option chain scheduler status"""
    status = get_indusindbk_option_chain_status()
    return jsonify(status)


@app.route('/api/indusindbk/data')
@token_required
def api_indusindbk_data():
    """API endpoint to get collected INDUSINDBK option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("INDUSINDBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for INDUSINDBK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/indusindbk/expiry')
def api_indusindbk_expiry():
    """API endpoint to get current INDUSINDBK expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("INDUSINDBK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "INDUSINDBK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "INDUSINDBK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "INDUSINDBK"
        }), 500


@app.route('/api/indusindbk/stats')
def api_indusindbk_stats():
    """API endpoint to get INDUSINDBK option chain statistics"""
    try:
        collector, collection = get_bank_collection("INDUSINDBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for INDUSINDBK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/indusindbk/trigger', methods=['POST'])
def api_indusindbk_trigger():
    """API endpoint to manually trigger INDUSINDBK option chain data collection"""
    try:
        collector, collection = get_bank_collection("INDUSINDBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for INDUSINDBK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "INDUSINDBK option chain data collection completed" if success else "INDUSINDBK option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/indusindbk/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_indusindbk_data_by_id(record_id):
    """API endpoint to get or delete a specific INDUSINDBK option chain record"""
    try:
        collector, collection = get_bank_collection("INDUSINDBK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for INDUSINDBK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# IDFCFIRSTB Option Chain Endpoints

def get_idfcfirstb_option_chain_next_run_time():
    """Calculate next scheduled run time for IDFCFIRSTB option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_idfcfirstb_option_chain_status():
    """Get IDFCFIRSTB option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_idfcfirstb_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract IDFCFIRSTB specific result if available
                if "results" in file_status and "IDFCFIRSTB" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["IDFCFIRSTB"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/idfcfirstb/status')
def api_idfcfirstb_status():
    """API endpoint to get IDFCFIRSTB option chain scheduler status"""
    status = get_idfcfirstb_option_chain_status()
    return jsonify(status)


@app.route('/api/idfcfirstb/data')
@token_required
def api_idfcfirstb_data():
    """API endpoint to get collected IDFCFIRSTB option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("IDFCFIRSTB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for IDFCFIRSTB"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/idfcfirstb/expiry')
def api_idfcfirstb_expiry():
    """API endpoint to get current IDFCFIRSTB expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("IDFCFIRSTB")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "IDFCFIRSTB"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "IDFCFIRSTB"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "IDFCFIRSTB"
        }), 500


@app.route('/api/idfcfirstb/stats')
def api_idfcfirstb_stats():
    """API endpoint to get IDFCFIRSTB option chain statistics"""
    try:
        collector, collection = get_bank_collection("IDFCFIRSTB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for IDFCFIRSTB"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/idfcfirstb/trigger', methods=['POST'])
def api_idfcfirstb_trigger():
    """API endpoint to manually trigger IDFCFIRSTB option chain data collection"""
    try:
        collector, collection = get_bank_collection("IDFCFIRSTB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for IDFCFIRSTB"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "IDFCFIRSTB option chain data collection completed" if success else "IDFCFIRSTB option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/idfcfirstb/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_idfcfirstb_data_by_id(record_id):
    """API endpoint to get or delete a specific IDFCFIRSTB option chain record"""
    try:
        collector, collection = get_bank_collection("IDFCFIRSTB")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for IDFCFIRSTB"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# FEDERALBNK Option Chain Endpoints

def get_federalbnk_option_chain_next_run_time():
    """Calculate next scheduled run time for FEDERALBNK option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_federalbnk_option_chain_status():
    """Get FEDERALBNK option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('all_banks_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_federalbnk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read unified status file
    if os.path.exists(ALL_BANKS_STATUS_FILE):
        try:
            with open(ALL_BANKS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                # Extract FEDERALBNK specific result if available
                if "results" in file_status and "FEDERALBNK" in file_status["results"]:
                    status["last_status"] = "success" if file_status["results"]["FEDERALBNK"] else "failed"
                else:
                    status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/federalbnk/status')
def api_federalbnk_status():
    """API endpoint to get FEDERALBNK option chain scheduler status"""
    status = get_federalbnk_option_chain_status()
    return jsonify(status)


@app.route('/api/federalbnk/data')
@token_required
def api_federalbnk_data():
    """API endpoint to get collected FEDERALBNK option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector, collection = get_bank_collection("FEDERALBNK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FEDERALBNK"
            }), 404
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            records_data = record.get("records", {})
            timestamp = records_data.get("timestamp") if isinstance(records_data, dict) else None
            underlying_value = records_data.get("underlyingValue") if isinstance(records_data, dict) else None
            data_array = records_data.get("data", []) if isinstance(records_data, dict) else []
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp,
                "underlyingValue": underlying_value,
                "dataCount": len(data_array) if isinstance(data_array, list) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/federalbnk/expiry')
def api_federalbnk_expiry():
    """API endpoint to get current FEDERALBNK expiry date"""
    try:
        collector = NSEAllBanksOptionChainCollector()
        expiry = collector._fetch_expiry_dates_with_retry("FEDERALBNK")
        collector.close()
        
        if expiry:
            return jsonify({
                "success": True,
                "expiry": expiry,
                "symbol": "FEDERALBNK"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch expiry date",
                "expiry": None,
                "symbol": "FEDERALBNK"
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "expiry": None,
            "symbol": "FEDERALBNK"
        }), 500


@app.route('/api/federalbnk/stats')
def api_federalbnk_stats():
    """API endpoint to get FEDERALBNK option chain statistics"""
    try:
        collector, collection = get_bank_collection("FEDERALBNK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FEDERALBNK"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest_record = collection.find_one(sort=[("records.timestamp", -1)])
        latest_timestamp = None
        latest_underlying = None
        if latest_record:
            records_data = latest_record.get("records", {})
            if isinstance(records_data, dict):
                latest_timestamp = records_data.get("timestamp")
                latest_underlying = records_data.get("underlyingValue")
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_underlying_value": latest_underlying
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/federalbnk/trigger', methods=['POST'])
def api_federalbnk_trigger():
    """API endpoint to manually trigger FEDERALBNK option chain data collection"""
    try:
        collector, collection = get_bank_collection("FEDERALBNK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FEDERALBNK"
            }), 404
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        # Status is now managed by unified scheduler
        
        return jsonify({
            "success": success,
            "message": "FEDERALBNK option chain data collection completed" if success else "FEDERALBNK option chain data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/federalbnk/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_federalbnk_data_by_id(record_id):
    """API endpoint to get or delete a specific FEDERALBNK option chain record"""
    try:
        collector, collection = get_bank_collection("FEDERALBNK")
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for FEDERALBNK"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "records": record.get("records", {}),
                "filtered": record.get("filtered", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Top 20 Gainers Endpoints

def get_gainers_next_run_time():
    """Calculate next scheduled run time for gainers using config"""
    return get_interval_scheduler_next_run_time("gainers")


def get_gainers_status():
    """Get gainers status from separate scheduler status file"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('gainers_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_gainers_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    status_file = 'gainers_scheduler_status.json'
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
                status["success"] = file_status.get("success", None)
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/gainers/status')
def api_gainers_status():
    """API endpoint to get gainers scheduler status"""
    status = get_gainers_status()
    return jsonify(status)


@app.route('/api/gainers/data')
@token_required
def api_gainers_data():
    """API endpoint to get collected gainers data with pagination and date filtering"""
    try:
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query_filter:
                query_filter["timestamp"]["$lte"] = end_date
            else:
                query_filter["timestamp"] = {"$lte": end_date}
        
        skip = (page - 1) * limit
        
        collector, collection = get_gainers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for gainers"
            }), 404
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            # Get timestamp from record (could be in various places)
            timestamp = None
            for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                if key in record and isinstance(record[key], dict):
                    section_timestamp = record[key].get('timestamp')
                    if section_timestamp:
                        timestamp = section_timestamp
                        break
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp or record.get("timestamp"),
                "legends": record.get("legends", []),
                "nifty_count": len(record.get("NIFTY", {}).get("data", [])) if isinstance(record.get("NIFTY"), dict) else 0,
                "banknifty_count": len(record.get("BANKNIFTY", {}).get("data", [])) if isinstance(record.get("BANKNIFTY"), dict) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/gainers/stats')
def api_gainers_stats():
    """API endpoint to get gainers statistics"""
    try:
        collector, collection = get_gainers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for gainers"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("timestamp", -1)])
        
        latest_timestamp = None
        nifty_count = 0
        banknifty_count = 0
        if latest:
            # Get timestamp from latest record
            for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                if key in latest and isinstance(latest[key], dict):
                    section_timestamp = latest[key].get('timestamp')
                    if section_timestamp:
                        latest_timestamp = section_timestamp
                        break
            
            if isinstance(latest.get("NIFTY"), dict):
                nifty_count = len(latest.get("NIFTY", {}).get("data", []))
            if isinstance(latest.get("BANKNIFTY"), dict):
                banknifty_count = len(latest.get("BANKNIFTY", {}).get("data", []))
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_nifty_count": nifty_count,
            "latest_banknifty_count": banknifty_count
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/gainers/trigger', methods=['POST'])
def api_gainers_trigger():
    """API endpoint to manually trigger gainers data collection"""
    try:
        collector = NSEAllGainersLosersCollector()
        success = collector.collect_and_save_single("gainers")
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "Gainers data collection completed" if success else "Gainers data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/gainers/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_gainers_data_by_id(record_id):
    """API endpoint to get or delete a specific gainers record"""
    try:
        collector, collection = get_gainers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for gainers"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": record.get("timestamp"),
                "legends": record.get("legends", []),
                "NIFTY": record.get("NIFTY", {}),
                "BANKNIFTY": record.get("BANKNIFTY", {}),
                "NIFTYNEXT50": record.get("NIFTYNEXT50", {}),
                "allSec": record.get("allSec", {}),
                "FOSec": record.get("FOSec", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Top 20 Losers Endpoints

def get_losers_next_run_time():
    """Calculate next scheduled run time for losers using config"""
    return get_interval_scheduler_next_run_time("losers")


def get_losers_status():
    """Get losers status from separate scheduler status file"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('losers_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_losers_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    status_file = 'losers_scheduler_status.json'
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
                status["success"] = file_status.get("success", None)
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/losers/status')
def api_losers_status():
    """API endpoint to get losers scheduler status"""
    status = get_losers_status()
    return jsonify(status)


@app.route('/api/losers/data')
@token_required
def api_losers_data():
    """API endpoint to get collected losers data with pagination and date filtering"""
    try:
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["timestamp"] = {"$gte": start_date}
        if end_date:
            if "timestamp" in query_filter:
                query_filter["timestamp"]["$lte"] = end_date
            else:
                query_filter["timestamp"] = {"$lte": end_date}
        
        skip = (page - 1) * limit
        
        collector, collection = get_losers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for losers"
            }), 404
        
        # Get total count with filter
        total_count = collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collection.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            # Get timestamp from record (could be in various places)
            timestamp = None
            for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                if key in record and isinstance(record[key], dict):
                    section_timestamp = record[key].get('timestamp')
                    if section_timestamp:
                        timestamp = section_timestamp
                        break
            
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": timestamp or record.get("timestamp"),
                "legends": record.get("legends", []),
                "nifty_count": len(record.get("NIFTY", {}).get("data", [])) if isinstance(record.get("NIFTY"), dict) else 0,
                "banknifty_count": len(record.get("BANKNIFTY", {}).get("data", [])) if isinstance(record.get("BANKNIFTY"), dict) else 0,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/losers/stats')
def api_losers_stats():
    """API endpoint to get losers statistics"""
    try:
        collector, collection = get_losers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for losers"
            }), 404
        
        total_count = collection.count_documents({})
        
        # Get latest record
        latest = collection.find_one(sort=[("timestamp", -1)])
        
        latest_timestamp = None
        nifty_count = 0
        banknifty_count = 0
        if latest:
            # Get timestamp from latest record
            for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                if key in latest and isinstance(latest[key], dict):
                    section_timestamp = latest[key].get('timestamp')
                    if section_timestamp:
                        latest_timestamp = section_timestamp
                        break
            
            if isinstance(latest.get("NIFTY"), dict):
                nifty_count = len(latest.get("NIFTY", {}).get("data", []))
            if isinstance(latest.get("BANKNIFTY"), dict):
                banknifty_count = len(latest.get("BANKNIFTY", {}).get("data", []))
        
        stats = {
            "total_records": total_count,
            "latest_timestamp": latest_timestamp,
            "latest_nifty_count": nifty_count,
            "latest_banknifty_count": banknifty_count
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/losers/trigger', methods=['POST'])
def api_losers_trigger():
    """API endpoint to manually trigger losers data collection"""
    try:
        collector = NSEAllGainersLosersCollector()
        success = collector.collect_and_save_single("losers")
        collector.close()
        
        return jsonify({
            "success": success,
            "message": "Losers data collection completed" if success else "Losers data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/losers/data/<record_id>', methods=['GET', 'DELETE'])
@token_required
def api_losers_data_by_id(record_id):
    """API endpoint to get or delete a specific losers record"""
    try:
        collector, collection = get_losers_collection()
        if collection is None:
            collector.close()
            return jsonify({
                "success": False,
                "error": "Collection not found for losers"
            }), 404
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collection.find_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if not record:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            # Convert ObjectId to string and format dates
            record_dict = {
                "_id": str(record.get("_id")),
                "timestamp": record.get("timestamp"),
                "legends": record.get("legends", []),
                "NIFTY": record.get("NIFTY", {}),
                "BANKNIFTY": record.get("BANKNIFTY", {}),
                "NIFTYNEXT50": record.get("NIFTYNEXT50", {}),
                "allSec": record.get("allSec", {}),
                "FOSec": record.get("FOSec", {}),
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None,
                "updatedAt": record.get("updatedAt").isoformat() if record.get("updatedAt") else None
            }
            
            return jsonify({
                "success": True,
                "data": record_dict
            })
        
        elif request.method == 'DELETE':
            result = collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# News Collector Endpoints

def get_news_collector_next_run_time():
    """Calculate next scheduled run time for news collector using config"""
    return get_interval_scheduler_next_run_time("news")


def get_news_collector_status():
    """Get news collector scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('news_collector_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_news_collector_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(NEWS_COLLECTOR_STATUS_FILE):
        try:
            with open(NEWS_COLLECTOR_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/news/status')
def api_news_status():
    """API endpoint to get news collector scheduler status"""
    status = get_news_collector_status()
    return jsonify(status)


@app.route('/api/news/data')
@token_required
def api_news_data():
    """API endpoint to get collected news data with pagination and date filtering"""
    try:
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query_filter:
                query_filter["date"]["$lte"] = end_date
            else:
                query_filter["date"] = {"$lte": end_date}
        
        skip = (page - 1) * limit
        
        collector = NSENewsCollector()
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by pub_date (newest first)
        records = list(collector.collection.find(query_filter).sort("pub_date", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            record_dict = {
                "_id": str(record.get("_id")),
                "date": record.get("date"),
                "keyword": record.get("keyword"),
                "title": record.get("title"),
                "source": record.get("source"),
                "sentiment": record.get("sentiment"),
                "link": record.get("link"),
                "pub_date": record.get("pub_date").isoformat() if record.get("pub_date") else None,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/news/stats')
def api_news_stats():
    """API endpoint to get news statistics"""
    try:
        collector = NSENewsCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get today's date
        from datetime import datetime
        import pytz
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).date().isoformat()
        
        # Count by sentiment
        positive_count = collector.collection.count_documents({"sentiment": "Positive", "date": today})
        negative_count = collector.collection.count_documents({"sentiment": "Negative", "date": today})
        neutral_count = collector.collection.count_documents({"sentiment": "Neutral", "date": today})
        
        # Count by keyword (top keywords)
        keyword_pipeline = [
            {"$match": {"date": today}},
            {"$group": {"_id": "$keyword", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_keywords = list(collector.collection.aggregate(keyword_pipeline))
        
        stats = {
            "total_records": total_count,
            "today_count": collector.collection.count_documents({"date": today}),
            "today_positive": positive_count,
            "today_negative": negative_count,
            "today_neutral": neutral_count,
            "top_keywords": [{"keyword": item["_id"], "count": item["count"]} for item in top_keywords]
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/news/trigger', methods=['POST'])
def api_news_trigger():
    """API endpoint to manually trigger news collection"""
    try:
        
        collector = NSENewsCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(NEWS_COLLECTOR_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
        return jsonify({
            "success": success,
            "message": "News collection completed" if success else "News collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/news/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_news_data(record_id):
    """API endpoint to delete a specific news record"""
    try:
        collector = NSENewsCollector()
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        elif request.method == 'DELETE':
            result = collector.collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Twitter collector endpoints removed - not needed


# ==================== LiveMint News Collector Endpoints ====================

def get_livemint_news_collector_next_run_time():
    """Calculate next scheduled run time for LiveMint news collector using config"""
    return get_interval_scheduler_next_run_time("news")


def get_livemint_news_collector_status():
    """Get LiveMint news collector scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('livemint_news_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_livemint_news_collector_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(LIVEMINT_NEWS_STATUS_FILE):
        try:
            with open(LIVEMINT_NEWS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/livemint-news/status')
@token_required
def api_livemint_news_status():
    """API endpoint to get LiveMint news collector scheduler status"""
    status = get_livemint_news_collector_status()
    return jsonify(status)


@app.route('/api/livemint-news/data')
@token_required
def api_livemint_news_data():
    """API endpoint to get collected LiveMint news data with pagination and date filtering"""
    try:
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            query_filter["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query_filter:
                query_filter["date"]["$lte"] = end_date
            else:
                query_filter["date"] = {"$lte": end_date}
        
        skip = (page - 1) * limit
        
        collector = NSELiveMintNewsCollector()
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by pub_date (newest first)
        records = list(collector.collection.find(query_filter).sort("pub_date", -1).skip(skip).limit(limit))
        
        # Convert ObjectId to string and format dates
        data = []
        for record in records:
            record_dict = {
                "_id": str(record.get("_id")),
                "date": record.get("date"),
                "source": record.get("source"),
                "title": record.get("title"),
                "description": record.get("description"),
                "source_type": record.get("source_type"),
                "sentiment": record.get("sentiment"),
                "link": record.get("link"),
                "image_url": record.get("image_url"),
                "pub_date": record.get("pub_date").isoformat() if record.get("pub_date") else None,
                "insertedAt": record.get("insertedAt").isoformat() if record.get("insertedAt") else None
            }
            data.append(record_dict)
        
        collector.close()
        
        total_pages = (total_count + limit - 1) // limit
        
        return jsonify({
            "success": True,
            "count": len(data),
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/livemint-news/stats')
@token_required
def api_livemint_news_stats():
    """API endpoint to get LiveMint news statistics"""
    try:
        collector = NSELiveMintNewsCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get today's date
        import pytz
        ist = pytz.timezone("Asia/Kolkata")
        today = datetime.now(ist).date().isoformat()
        
        # Count by sentiment
        positive_count = collector.collection.count_documents({"sentiment": "Positive", "date": today})
        negative_count = collector.collection.count_documents({"sentiment": "Negative", "date": today})
        neutral_count = collector.collection.count_documents({"sentiment": "Neutral", "date": today})
        
        stats = {
            "total_records": total_count,
            "today_count": collector.collection.count_documents({"date": today}),
            "today_positive": positive_count,
            "today_negative": negative_count,
            "today_neutral": neutral_count
        }
        
        collector.close()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/livemint-news/trigger', methods=['POST'])
@token_required
def api_livemint_news_trigger():
    """API endpoint to manually trigger LiveMint news collection"""
    try:
        collector = NSELiveMintNewsCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(LIVEMINT_NEWS_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
        return jsonify({
            "success": success,
            "message": "LiveMint news collection completed" if success else "LiveMint news collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/livemint-news/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_livemint_news_data(record_id):
    """API endpoint to delete a specific LiveMint news record"""
    try:
        collector = NSELiveMintNewsCollector()
        
        if not ObjectId.is_valid(record_id):
            collector.close()
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        elif request.method == 'DELETE':
            result = collector.collection.delete_one({"_id": ObjectId(record_id)})
            collector.close()
            
            if result.deleted_count == 0:
                return jsonify({
                    "success": False,
                    "error": "Record not found"
                }), 404
            
            return jsonify({
                "success": True,
                "message": "Record deleted successfully"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Configuration Management API Endpoints
# ============================================================================

@app.route('/api/config', methods=['GET'])
@token_required
def api_get_config():
    """Get all scheduler configurations"""
    try:
        config = get_all_config()
        return jsonify({
            "success": True,
            "config": config
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/config', methods=['POST'])
@token_required
@validate_json_body(SchedulerConfigSchema)
def api_update_config(validated_data):
    """Update scheduler configuration"""
    try:
        scheduler_type = validated_data['scheduler_type']
        config_updates = validated_data['config']
        
        # Get existing config to merge with updates for validation
        existing_config = get_config_for_scheduler(scheduler_type) or {}
        
        # Merge existing config with updates to validate complete config
        merged_config = {**existing_config, **config_updates}
        
        # Validate config updates using ConfigUpdateSchema
        # Pass both start_time and end_time in context for proper validation
        config_schema = ConfigUpdateSchema(context={
            'start_time': merged_config.get('start_time'),
            'end_time': merged_config.get('end_time')
        })
        try:
            validated_config = config_schema.load(config_updates)
        except ValidationError as err:
            return jsonify({
                "success": False,
                "error": "Invalid config values",
                "errors": err.messages
            }), 400
        
        # Additional validation: check if end_time is after start_time in merged config
        if 'start_time' in merged_config and 'end_time' in merged_config:
            from datetime import datetime
            start = datetime.strptime(merged_config['start_time'], '%H:%M').time()
            end = datetime.strptime(merged_config['end_time'], '%H:%M').time()
            if end <= start:
                return jsonify({
                    "success": False,
                    "error": "Invalid time range",
                    "errors": {"end_time": ["end_time must be after start_time"]}
                }), 400
        
        # Update configuration with validated data
        success = update_scheduler_config(scheduler_type, validated_config)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Configuration updated for {scheduler_type}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update configuration"
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/holidays', methods=['GET'])
@token_required
def api_get_holidays():
    """Get all holidays"""
    try:
        holidays = get_holidays()
        return jsonify({
            "success": True,
            "holidays": holidays
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/holidays', methods=['POST'])
@token_required
@validate_json_body(HolidaySchema)
def api_add_holiday(validated_data):
    """Add a holiday"""
    try:
        holiday_date = validated_data['date']
        
        success = add_holiday(holiday_date)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Holiday {holiday_date} added successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to add holiday. Invalid date format."
            }), 400
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/holidays', methods=['DELETE'])
@token_required
@validate_json_body(HolidaySchema)
def api_remove_holiday(validated_data):
    """Remove a holiday"""
    try:
        holiday_date = validated_data['date']
        
        success = remove_holiday(holiday_date)
        
        return jsonify({
            "success": True,
            "message": f"Holiday {holiday_date} removed successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Global variable to track scheduler threads
_scheduler_threads = []
_scheduler_watchdog_thread = None
_scheduler_config = [
    ('cronjob_scheduler', 'FII/DII Data Collector'),
    ('all_indices_option_chain_scheduler', 'All Indices Option Chain Collector (4 indices)'),
    ('all_banks_option_chain_scheduler', 'All Banks Option Chain Collector (12 banks)'),
    ('gainers_scheduler', 'Top 20 Gainers Collector'),
    ('losers_scheduler', 'Top 20 Losers Collector'),
    ('news_collector_scheduler', 'News Collector'),
    ('livemint_news_scheduler', 'LiveMint News Collector'),
]

def run_scheduler_in_thread(module_name, scheduler_name, max_retries=3, retry_delay=30):
    """Run scheduler in a separate thread with auto-restart on failure"""
    def scheduler_worker():
        retry_count = 0
        while retry_count < max_retries:
            try:
                logger = get_logger(__name__)
                logger.info(f"Starting {scheduler_name}... (Attempt {retry_count + 1}/{max_retries})")
                
                # Ensure we're in the correct directory for imports
                import sys
                import os
                backend_dir = os.path.dirname(os.path.abspath(__file__))
                if backend_dir not in sys.path:
                    sys.path.insert(0, backend_dir)
                
                # Import the scheduler module
                logger.info(f"Importing module: {module_name}")
                scheduler_module = __import__(module_name, fromlist=[])
                logger.info(f"{scheduler_name} module imported successfully")
                
                # Check if module has a main function (most schedulers have this)
                if hasattr(scheduler_module, 'main'):
                    logger.info(f"{scheduler_name} has main() function, calling it...")
                    # Reset retry count on successful start
                    retry_count = 0
                    scheduler_module.main()
                    # If main() returns, it means the scheduler stopped normally
                    logger.warning(f"{scheduler_name} main() function returned. Scheduler may have stopped.")
                    break
                else:
                    logger.error(f"{scheduler_name} does not have a main() function")
                    break
                
            except ImportError as e:
                logger = get_logger(__name__)
                logger.error(f"Failed to import {module_name}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying {scheduler_name} in {retry_delay} seconds...")
                    time_module.sleep(retry_delay)
                else:
                    logger.error(f"{scheduler_name} failed after {max_retries} attempts. Giving up.")
                    break
            except KeyboardInterrupt:
                logger = get_logger(__name__)
                logger.info(f"{scheduler_name} stopped by user")
                break
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error in {scheduler_name} thread: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"{scheduler_name} crashed. Restarting in {retry_delay} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    time_module.sleep(retry_delay)
                else:
                    logger.error(f"{scheduler_name} failed after {max_retries} attempts. Will be restarted by watchdog.")
                    # Don't break - let watchdog restart it
                    time_module.sleep(60)  # Wait before retry (watchdog will handle)
                    retry_count = 0  # Reset for watchdog restart
        
        logger = get_logger(__name__)
        logger.error(f"{scheduler_name} worker thread exited")
    
    thread = threading.Thread(target=scheduler_worker, daemon=True, name=scheduler_name)
    thread.start()
    logger = get_logger(__name__)
    logger.info(f"Thread started for {scheduler_name} (daemon thread, ID: {thread.ident})")
    return thread

def start_scheduler_watchdog():
    """Start a watchdog thread that monitors and restarts dead schedulers"""
    global _scheduler_threads, _scheduler_watchdog_thread, _scheduler_config
    
    def watchdog_worker():
        logger = get_logger(__name__)
        logger.info("Scheduler watchdog started. Monitoring schedulers every 60 seconds...")
        
        while True:
            try:
                time_module.sleep(60)  # Check every minute
                
                if not _scheduler_threads:
                    continue
                
                # Check each scheduler thread
                for i, (thread, name) in enumerate(_scheduler_threads):
                    if not thread.is_alive():
                        logger.warning(f"⚠️  {name} thread is DEAD. Restarting...")
                        
                        # Find the module name for this scheduler
                        module_name = None
                        for mod_name, sched_name in _scheduler_config:
                            if sched_name == name:
                                module_name = mod_name
                                break
                        
                        if module_name:
                            # Restart the scheduler
                            try:
                                new_thread = run_scheduler_in_thread(module_name, name, max_retries=3, retry_delay=30)
                                _scheduler_threads[i] = (new_thread, name)
                                logger.info(f"✓ {name} restarted successfully (New Thread ID: {new_thread.ident})")
                            except Exception as e:
                                logger.error(f"Failed to restart {name}: {str(e)}")
                        else:
                            logger.error(f"Could not find module name for {name}")
                
                # Log status every 5 minutes
                if int(time_module.time()) % 300 == 0:  # Every 5 minutes
                    alive_count = sum(1 for thread, name in _scheduler_threads if thread.is_alive())
                    logger.info(f"Watchdog status: {alive_count}/{len(_scheduler_threads)} schedulers alive")
                    
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(f"Error in watchdog thread: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
    
    _scheduler_watchdog_thread = threading.Thread(target=watchdog_worker, daemon=True, name="SchedulerWatchdog")
    _scheduler_watchdog_thread.start()
    logger = get_logger(__name__)
    logger.info("Scheduler watchdog thread started")

def start_all_schedulers_in_background():
    """Start all schedulers in background threads"""
    global _scheduler_threads, _scheduler_config
    
    # Use centralized logging configuration
    logger = get_logger(__name__)
    
    logger.info("Starting All Data Collectors in Background")
    logger.debug(f"Started at: {datetime.now()}")
    
    # Use the global scheduler config
    schedulers = _scheduler_config
    
    threads = []
    
    # Start each scheduler in a separate thread
    for module_name, scheduler_name in schedulers:
        try:
            logger.info(f"Attempting to start {scheduler_name} ({module_name})...")
            thread = run_scheduler_in_thread(module_name, scheduler_name, max_retries=3, retry_delay=30)
            threads.append((thread, scheduler_name))
            logger.info(f"✓ {scheduler_name} thread created successfully")
            time_module.sleep(0.5)  # Small delay between starting schedulers
        except Exception as e:
            logger.error(f"Failed to start {scheduler_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    _scheduler_threads = threads
    logger.info(f"All {len(threads)} scheduler threads created")
    
    # Start watchdog if not already running
    global _scheduler_watchdog_thread
    if _scheduler_watchdog_thread is None or not _scheduler_watchdog_thread.is_alive():
        start_scheduler_watchdog()
    
    # Wait a moment for threads to initialize
    time_module.sleep(1)
    
    # Verify threads are alive
    alive_count = sum(1 for thread, name in threads if thread.is_alive())
    logger.info(f"Active scheduler threads: {alive_count}/{len(threads)}")
    
    # Log which schedulers are alive
    for thread, name in threads:
        status = "✓ ALIVE" if thread.is_alive() else "✗ DEAD"
        logger.info(f"  {status} - {name} (Thread ID: {thread.ident})")
    
    if alive_count < len(threads):
        logger.warning(f"Warning: {len(threads) - alive_count} scheduler(s) failed to start! Watchdog will attempt to restart them.")
    
    return threads


@app.route('/api/schedulers/start', methods=['POST'])
@token_required
def api_start_schedulers():
    """API endpoint to start all schedulers"""
    try:
        global _scheduler_threads
        
        # Check if schedulers are already running
        alive_count = sum(1 for thread, name in _scheduler_threads if thread.is_alive()) if _scheduler_threads else 0
        
        if alive_count > 0:
            return jsonify({
                "success": True,
                "message": f"Schedulers already running ({alive_count} active)",
                "already_running": True
            })
        
        # Start schedulers
        threads = start_all_schedulers_in_background()
        
        return jsonify({
            "success": True,
            "message": f"All {len(threads)} schedulers started successfully",
            "count": len(threads)
        })
    except Exception as e:
        logger.error(f"Failed to start schedulers: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/schedulers/status', methods=['GET'])
@token_required
def api_schedulers_status():
    """API endpoint to get status of all scheduler threads"""
    try:
        global _scheduler_threads
        
        status_list = []
        
        if _scheduler_threads:
            for thread, name in _scheduler_threads:
                status_list.append({
                    "name": name,
                    "alive": thread.is_alive(),
                    "daemon": thread.daemon,
                    "thread_id": thread.ident
                })
        else:
            # Schedulers not started yet
            schedulers = [
                'FII/DII Data Collector',
                'All Indices Option Chain Collector (4 indices)',
                'All Banks Option Chain Collector (12 banks)',
                'Top 20 Gainers Collector',
                'Top 20 Losers Collector',
                'News Collector',
                'LiveMint News Collector',
            ]
            for name in schedulers:
                status_list.append({
                    "name": name,
                    "alive": False,
                    "daemon": False,
                    "thread_id": None
                })
        
        alive_count = sum(1 for s in status_list if s["alive"])
        total_count = len(status_list)
        
        return jsonify({
            "success": True,
            "total": total_count,
            "alive": alive_count,
            "stopped": total_count - alive_count,
            "schedulers": status_list
        })
    except Exception as e:
        logger.error(f"Failed to get scheduler status: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Auto-start schedulers when module is imported (if enabled)
# This allows schedulers to start even when using WSGI servers
# Set AUTO_START_SCHEDULERS=false in .env to disable
AUTO_START_SCHEDULERS = os.getenv('AUTO_START_SCHEDULERS', 'true').lower() == 'true'

if AUTO_START_SCHEDULERS:
    try:
        # Start schedulers automatically when module loads
        # This works for both direct execution and WSGI servers
        logger.info("=" * 80)
        logger.info("Auto-starting all schedulers...")
        logger.info("=" * 80)
        start_all_schedulers_in_background()
        logger.info("Schedulers auto-started on module load")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"Failed to auto-start schedulers: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    print("=" * 80)
    print("Starting Admin Panel...")
    print("=" * 80)
    
    # Schedulers are already started via AUTO_START_SCHEDULERS above
    if _scheduler_threads:
        alive_count = sum(1 for thread, name in _scheduler_threads if thread.is_alive())
        print(f"✓ {alive_count}/{len(_scheduler_threads)} schedulers running in background")
        if alive_count < len(_scheduler_threads):
            print(f"⚠ Warning: {len(_scheduler_threads) - alive_count} scheduler(s) failed to start")
            print("  Check logs for details")
    else:
        print("⚠ Schedulers not started. Use POST /api/schedulers/start to start them.")
    print("=" * 80)
    
    # Get host and port for display
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    # Display access URL based on host
    if host == '0.0.0.0':
        # Running on all interfaces - show both localhost and note about external access
        print(f"Access the panel at: http://localhost:{port} (local)")
        print(f"Server listening on: {host}:{port} (all interfaces)")
    else:
        print(f"Access the panel at: http://{host}:{port}")
    
    print("=" * 80)
    print("Press Ctrl+C to stop both admin panel and schedulers")
    print("=" * 80)
    
    # Run Flask app
    # In production, use a production WSGI server like gunicorn
    # For development: app.run(debug=True, host='0.0.0.0', port=5000)
    # For production: Use gunicorn or uWSGI
    app.run(debug=debug_mode, host=host, port=port)

