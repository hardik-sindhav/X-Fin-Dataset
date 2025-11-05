"""
Admin Panel for NSE FII/DII Data Collector
Web interface to monitor cronjob status and view data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId
from nse_fiidii_collector import NSEDataCollector
from nse_option_chain_collector import NSEOptionChainCollector
from scheduler_config import (
    get_all_config, get_config_for_scheduler, update_scheduler_config,
    get_holidays, add_holiday, remove_holiday, is_holiday
)
from nse_banknifty_option_chain_collector import NSEBankNiftyOptionChainCollector
from nse_finnifty_option_chain_collector import NSEFinniftyOptionChainCollector
from nse_midcpnifty_option_chain_collector import NSEMidcapNiftyOptionChainCollector
from nse_hdfcbank_option_chain_collector import NSEHDFCBankOptionChainCollector
from nse_icicibank_option_chain_collector import NSEICICIBankOptionChainCollector
from nse_sbin_option_chain_collector import NSESBINOptionChainCollector
from nse_kotakbank_option_chain_collector import NSEKotakBankOptionChainCollector
from nse_axisbank_option_chain_collector import NSEAxisBankOptionChainCollector
from nse_bankbaroda_option_chain_collector import NSEBankBarodaOptionChainCollector
from nse_pnb_option_chain_collector import NSEPNBOptionChainCollector
from nse_canbk_option_chain_collector import NSECANBKOptionChainCollector
from nse_aubank_option_chain_collector import NSEAUBANKOptionChainCollector
from nse_indusindbk_option_chain_collector import NSEIndusIndBkOptionChainCollector
from nse_idfcfirstb_option_chain_collector import NSEIDFCFIRSTBOptionChainCollector
from nse_federalbnk_option_chain_collector import NSEFEDERALBNKOptionChainCollector
from nse_gainers_collector import NSEGainersCollector
from nse_losers_collector import NSELosersCollector
from nse_news_collector import NSENewsCollector
from nse_livemint_news_collector import NSELiveMintNewsCollector

# Twitter collector removed - not needed
import schedule
import json
import os
from datetime import datetime, timedelta, time as dt_time
import threading
import time as time_module
import psutil
import sys
import jwt
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Default admin credentials (should be changed and stored securely in production)
# For production, use environment variables
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH', generate_password_hash('admin123'))

STATUS_FILE = 'scheduler_status.json'
OPTION_CHAIN_STATUS_FILE = 'option_chain_scheduler_status.json'
BANKNIFTY_STATUS_FILE = 'banknifty_option_chain_scheduler_status.json'
FINNIFTY_STATUS_FILE = 'finnifty_option_chain_scheduler_status.json'
MIDCPNIFTY_STATUS_FILE = 'midcpnifty_option_chain_scheduler_status.json'
HDFCBANK_STATUS_FILE = 'hdfcbank_option_chain_scheduler_status.json'
ICICIBANK_STATUS_FILE = 'icicibank_option_chain_scheduler_status.json'
SBIN_STATUS_FILE = 'sbin_option_chain_scheduler_status.json'
KOTAKBANK_STATUS_FILE = 'kotakbank_option_chain_scheduler_status.json'
AXISBANK_STATUS_FILE = 'axisbank_option_chain_scheduler_status.json'
BANKBARODA_STATUS_FILE = 'bankbaroda_option_chain_scheduler_status.json'
PNB_STATUS_FILE = 'pnb_option_chain_scheduler_status.json'
CANBK_STATUS_FILE = 'canbk_option_chain_scheduler_status.json'
AUBANK_STATUS_FILE = 'aubank_option_chain_scheduler_status.json'
INDUSINDBK_STATUS_FILE = 'indusindbk_option_chain_scheduler_status.json'
IDFCFIRSTB_STATUS_FILE = 'idfcfirstb_option_chain_scheduler_status.json'
FEDERALBNK_STATUS_FILE = 'federalbnk_option_chain_scheduler_status.json'
GAINERS_STATUS_FILE = 'gainers_scheduler_status.json'
LOSERS_STATUS_FILE = 'losers_scheduler_status.json'
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
def home():
    """Root endpoint to check if API is running"""
    return jsonify({"status": "ok", "message": "API is running"})


@app.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint for user login - returns JWT token"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # Verify credentials
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            # Generate JWT token
            token_payload = {
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
            }
            token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            
            return jsonify({
                'success': True,
                'token': token,
                'username': username,
                'expires_in': JWT_EXPIRATION_HOURS * 3600  # seconds
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
    status = get_scheduler_status()
    return jsonify(status)


@app.route('/api/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_data(record_id):
    """API endpoint to delete a specific FII/DII record"""
    try:
        collector = NSEDataCollector()
        
        # Validate ObjectId
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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
def api_data():
    """API endpoint to get collected data with pagination and date filtering"""
    try:
        collector = NSEDataCollector()
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Get date filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query filter
        query_filter = {}
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                query_filter["date"] = {"$gte": start_date}
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                if "date" in query_filter:
                    query_filter["date"]["$lte"] = end_date
                else:
                    query_filter["date"] = {"$lte": end_date}
            except ValueError:
                pass
        
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
            "last_run": datetime.now().isoformat(),
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
    scheduler_type: 'indices', 'banks', 'gainers_losers', 'news'
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
    
    # Check if process is running
    is_running, pid = check_scheduler_running('option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(OPTION_CHAIN_STATUS_FILE):
        try:
            with open(OPTION_CHAIN_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        collector = NSEOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEOptionChainCollector()
        
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
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("records.timestamp", -1)])
        
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
        collector = NSEOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(OPTION_CHAIN_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEOptionChainCollector()
        
        # Validate ObjectId
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            # Get the full record
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('banknifty_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_banknifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(BANKNIFTY_STATUS_FILE):
        try:
            with open(BANKNIFTY_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        collector = NSEBankNiftyOptionChainCollector()
        
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
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEBankNiftyOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEBankNiftyOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("records.timestamp", -1)])
        
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
        collector = NSEBankNiftyOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(BANKNIFTY_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEBankNiftyOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
        collector = NSEBankNiftyOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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
    is_running, pid = check_scheduler_running('finnifty_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_finnifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(FINNIFTY_STATUS_FILE):
        try:
            with open(FINNIFTY_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        collector = NSEFinniftyOptionChainCollector()
        
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
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEFinniftyOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEFinniftyOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("records.timestamp", -1)])
        
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
        collector = NSEFinniftyOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(FINNIFTY_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEFinniftyOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('midcpnifty_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_midcpnifty_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(MIDCPNIFTY_STATUS_FILE):
        try:
            with open(MIDCPNIFTY_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEMidcapNiftyOptionChainCollector()
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEMidcapNiftyOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEMidcapNiftyOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("records.timestamp", -1)])
        
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
        collector = NSEMidcapNiftyOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(MIDCPNIFTY_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEMidcapNiftyOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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


# HDFC Bank Option Chain Endpoints

def get_hdfcbank_option_chain_next_run_time():
    """Calculate next scheduled run time for HDFC Bank option chain using config"""
    return get_interval_scheduler_next_run_time("banks")


def get_hdfcbank_option_chain_status():
    """Get HDFC Bank option chain scheduler status from file or calculate"""
    status = {
        "running": False,
        "pid": None,
        "next_run": None,
        "last_run": None,
        "last_status": "unknown"
    }
    
    # Check if process is running
    is_running, pid = check_scheduler_running('hdfcbank_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_hdfcbank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(HDFCBANK_STATUS_FILE):
        try:
            with open(HDFCBANK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
        except Exception as e:
            pass
    
    # If scheduler is not running and we have no last run info, set default message
    if not status["running"] and not status["last_run"]:
        status["last_status"] = "not_started"
    
    return status


@app.route('/api/hdfcbank/status')
def api_hdfcbank_status():
    """API endpoint to get HDFC Bank option chain scheduler status"""
    status = get_hdfcbank_option_chain_status()
    return jsonify(status)


@app.route('/api/hdfcbank/data')
@token_required
def api_hdfcbank_data():
    """API endpoint to get collected HDFC Bank option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSEHDFCBankOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEHDFCBankOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEHDFCBankOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEHDFCBankOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(HDFCBANK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEHDFCBankOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    
    # Check if process is running
    is_running, pid = check_scheduler_running('icicibank_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_icicibank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(ICICIBANK_STATUS_FILE):
        try:
            with open(ICICIBANK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEICICIBankOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEICICIBankOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEICICIBankOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEICICIBankOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(ICICIBANK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEICICIBankOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('sbin_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_sbin_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(SBIN_STATUS_FILE):
        try:
            with open(SBIN_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSESBINOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSESBINOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSESBINOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSESBINOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(SBIN_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSESBINOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('kotakbank_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_kotakbank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(KOTAKBANK_STATUS_FILE):
        try:
            with open(KOTAKBANK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEKotakBankOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEKotakBankOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEKotakBankOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEKotakBankOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(KOTAKBANK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEKotakBankOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('axisbank_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_axisbank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(AXISBANK_STATUS_FILE):
        try:
            with open(AXISBANK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEAxisBankOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEAxisBankOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEAxisBankOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEAxisBankOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(AXISBANK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEAxisBankOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('bankbaroda_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_bankbaroda_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(BANKBARODA_STATUS_FILE):
        try:
            with open(BANKBARODA_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEBankBarodaOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEBankBarodaOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEBankBarodaOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEBankBarodaOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(BANKBARODA_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEBankBarodaOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('pnb_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_pnb_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(PNB_STATUS_FILE):
        try:
            with open(PNB_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEPNBOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEPNBOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEPNBOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEPNBOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(PNB_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEPNBOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('canbk_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_canbk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(CANBK_STATUS_FILE):
        try:
            with open(CANBK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSECANBKOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSECANBKOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSECANBKOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSECANBKOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(CANBK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSECANBKOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('aubank_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_aubank_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(AUBANK_STATUS_FILE):
        try:
            with open(AUBANK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEAUBANKOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEAUBANKOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEAUBANKOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEAUBANKOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(AUBANK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEAUBANKOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('indusindbk_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_indusindbk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(INDUSINDBK_STATUS_FILE):
        try:
            with open(INDUSINDBK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEIndusIndBkOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEIndusIndBkOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEIndusIndBkOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEIndusIndBkOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(INDUSINDBK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEIndusIndBkOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('idfcfirstb_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_idfcfirstb_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(IDFCFIRSTB_STATUS_FILE):
        try:
            with open(IDFCFIRSTB_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEIDFCFIRSTBOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEIDFCFIRSTBOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEIDFCFIRSTBOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEIDFCFIRSTBOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(IDFCFIRSTB_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEIDFCFIRSTBOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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
    is_running, pid = check_scheduler_running('federalbnk_option_chain_scheduler.py')
    status["running"] = is_running
    status["pid"] = pid
    
    # Get next run time
    try:
        next_run = get_federalbnk_option_chain_next_run_time()
        status["next_run"] = next_run.isoformat() if next_run else None
    except Exception as e:
        status["next_run"] = None
    
    # Try to read status file
    if os.path.exists(FEDERALBNK_STATUS_FILE):
        try:
            with open(FEDERALBNK_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
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
        
        collector = NSEFEDERALBNKOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEFEDERALBNKOptionChainCollector()
        expiry = collector.get_current_expiry()
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
        collector = NSEFEDERALBNKOptionChainCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest_record = collector.collection.find_one(sort=[("records.timestamp", -1)])
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
        collector = NSEFEDERALBNKOptionChainCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(FEDERALBNK_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
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
        collector = NSEFEDERALBNKOptionChainCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
        if request.method == 'GET':
            record = collector.collection.find_one({"_id": ObjectId(record_id)})
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


# Top 20 Gainers Endpoints

def get_gainers_next_run_time():
    """Calculate next scheduled run time for gainers using config"""
    return get_interval_scheduler_next_run_time("gainers_losers")


def get_gainers_status():
    """Get gainers scheduler status from file or calculate"""
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
    if os.path.exists(GAINERS_STATUS_FILE):
        try:
            with open(GAINERS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
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
        
        collector = NSEGainersCollector()
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSEGainersCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("timestamp", -1)])
        
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
        collector = NSEGainersCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(GAINERS_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
        return jsonify({
            "success": success,
            "message": "Gainers data collection completed" if success else "Gainers data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/gainers/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_gainers_data(record_id):
    """API endpoint to delete a specific gainers record"""
    try:
        collector = NSEGainersCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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


# Top 20 Losers Endpoints

def get_losers_next_run_time():
    """Calculate next scheduled run time for losers using config"""
    return get_interval_scheduler_next_run_time("gainers_losers")


def get_losers_status():
    """Get losers scheduler status from file or calculate"""
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
    if os.path.exists(LOSERS_STATUS_FILE):
        try:
            with open(LOSERS_STATUS_FILE, 'r') as f:
                file_status = json.load(f)
                status["last_run"] = file_status.get("last_run")
                status["last_status"] = file_status.get("last_status", "unknown")
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
        
        collector = NSELosersCollector()
        
        # Get total count with filter
        total_count = collector.collection.count_documents(query_filter)
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit))
        
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
        collector = NSELosersCollector()
        
        total_count = collector.collection.count_documents({})
        
        # Get latest record
        latest = collector.collection.find_one(sort=[("timestamp", -1)])
        
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
        collector = NSELosersCollector()
        success = collector.collect_and_save()
        collector.close()
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed",
            "manual_trigger": True
        }
        with open(LOSERS_STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
        
        return jsonify({
            "success": success,
            "message": "Losers data collection completed" if success else "Losers data collection failed"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/losers/data/<record_id>', methods=['DELETE'])
@token_required
def api_delete_losers_data(record_id):
    """API endpoint to delete a specific losers record"""
    try:
        collector = NSELosersCollector()
        
        if not ObjectId.is_valid(record_id):
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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
            "last_run": datetime.now().isoformat(),
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
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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
            "last_run": datetime.now().isoformat(),
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
            return jsonify({
                "success": False,
                "error": "Invalid record ID"
            }), 400
        
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
def api_update_config():
    """Update scheduler configuration"""
    try:
        data = request.get_json()
        scheduler_type = data.get('scheduler_type')  # 'banks', 'indices', etc.
        config_updates = data.get('config', {})
        
        if not scheduler_type:
            return jsonify({
                "success": False,
                "error": "scheduler_type is required"
            }), 400
        
        # Validate scheduler type
        valid_types = ['banks', 'indices', 'gainers_losers', 'news', 'fiidii']
        if scheduler_type not in valid_types:
            return jsonify({
                "success": False,
                "error": f"Invalid scheduler_type. Must be one of: {', '.join(valid_types)}"
            }), 400
        
        # Validate config updates
        if 'interval_minutes' in config_updates:
            try:
                interval = int(config_updates['interval_minutes'])
                if interval < 1:
                    return jsonify({
                        "success": False,
                        "error": "interval_minutes must be at least 1"
                    }), 400
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "interval_minutes must be a number"
                }), 400
        
        if 'start_time' in config_updates:
            try:
                datetime.strptime(config_updates['start_time'], "%H:%M")
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "start_time must be in HH:MM format"
                }), 400
        
        if 'end_time' in config_updates:
            try:
                datetime.strptime(config_updates['end_time'], "%H:%M")
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "end_time must be in HH:MM format"
                }), 400
        
        if 'enabled' in config_updates:
            if not isinstance(config_updates['enabled'], bool):
                return jsonify({
                    "success": False,
                    "error": "enabled must be a boolean"
                }), 400
        
        # Update configuration
        success = update_scheduler_config(scheduler_type, config_updates)
        
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
def api_add_holiday():
    """Add a holiday"""
    try:
        data = request.get_json()
        holiday_date = data.get('date')
        
        if not holiday_date:
            return jsonify({
                "success": False,
                "error": "date is required (format: YYYY-MM-DD)"
            }), 400
        
        # Validate date format
        try:
            datetime.strptime(holiday_date, "%Y-%m-%d")
        except ValueError:
            return jsonify({
                "success": False,
                "error": "date must be in YYYY-MM-DD format"
            }), 400
        
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
def api_remove_holiday():
    """Remove a holiday"""
    try:
        data = request.get_json()
        holiday_date = data.get('date')
        
        if not holiday_date:
            return jsonify({
                "success": False,
                "error": "date is required (format: YYYY-MM-DD)"
            }), 400
        
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


def start_all_schedulers_in_background():
    """Start all schedulers in background threads"""
    import logging
    
    # Configure logging for schedulers - Only show warnings and errors
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Console only - no log files
        ]
    )
    logger = logging.getLogger(__name__)
    
    # ADMIN PANEL: Starting All Data Collectors in Background
    # Started at: {datetime.now()}
    
    # List of all schedulers
    schedulers = [
        ('cronjob_scheduler', 'FII/DII Data Collector'),
        ('option_chain_scheduler', 'NIFTY Option Chain Collector'),
        ('banknifty_option_chain_scheduler', 'BankNifty Option Chain Collector'),
        ('finnifty_option_chain_scheduler', 'Finnifty Option Chain Collector'),
        ('midcpnifty_option_chain_scheduler', 'MidcapNifty Option Chain Collector'),
        ('hdfcbank_option_chain_scheduler', 'HDFC Bank Option Chain Collector'),
        ('icicibank_option_chain_scheduler', 'ICICI Bank Option Chain Collector'),
        ('sbin_option_chain_scheduler', 'SBIN Option Chain Collector'),
        ('kotakbank_option_chain_scheduler', 'Kotak Bank Option Chain Collector'),
        ('axisbank_option_chain_scheduler', 'Axis Bank Option Chain Collector'),
        ('bankbaroda_option_chain_scheduler', 'Bank of Baroda Option Chain Collector'),
        ('pnb_option_chain_scheduler', 'PNB Option Chain Collector'),
        ('canbk_option_chain_scheduler', 'CANBK Option Chain Collector'),
        ('aubank_option_chain_scheduler', 'AUBANK Option Chain Collector'),
        ('indusindbk_option_chain_scheduler', 'IndusInd Bank Option Chain Collector'),
        ('idfcfirstb_option_chain_scheduler', 'IDFC First Bank Option Chain Collector'),
        ('federalbnk_option_chain_scheduler', 'Federal Bank Option Chain Collector'),
        ('gainers_scheduler', 'Top 20 Gainers Collector'),
        ('losers_scheduler', 'Top 20 Losers Collector'),
        ('news_collector_scheduler', 'News Collector'),
        ('livemint_news_scheduler', 'LiveMint News Collector'),
    ]
    
    def run_scheduler_in_thread(module_name, scheduler_name):
        """Run scheduler in a separate thread"""
        def scheduler_worker():
            try:
                # Import the scheduler module
                scheduler_module = __import__(module_name, fromlist=[])
                
                # Check if module has a main function (most schedulers have this)
                if hasattr(scheduler_module, 'main'):
                    scheduler_module.main()
                else:
                    logger.error(f"{scheduler_name} does not have a main() function")
                
            except ImportError as e:
                logger.error(f"Failed to import {module_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Error in {scheduler_name} thread: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        thread = threading.Thread(target=scheduler_worker, daemon=True, name=scheduler_name)
        thread.start()
        return thread
    
    threads = []
    
    # Start each scheduler in a separate thread
    for module_name, scheduler_name in schedulers:
        thread = run_scheduler_in_thread(module_name, scheduler_name)
        threads.append((thread, scheduler_name))
        time_module.sleep(0.5)  # Small delay between starting schedulers
    
    # All {len(threads)} schedulers started successfully in background!
    
    return threads


if __name__ == '__main__':
    print("=" * 80)
    print("Starting Admin Panel...")
    print("=" * 80)
    print("Starting all data collectors automatically...")
    
    # Start all schedulers in background threads
    scheduler_threads = start_all_schedulers_in_background()
    
    print(f"✓ All {len(scheduler_threads)} schedulers started in background")
    print("=" * 80)
    print("Access the panel at: http://localhost:5000")
    print("=" * 80)
    print("Press Ctrl+C to stop both admin panel and schedulers")
    print("=" * 80)
    
    # Run Flask app
    # In production, use a production WSGI server like gunicorn
    # For development: app.run(debug=True, host='0.0.0.0', port=5000)
    # For production: Use gunicorn or uWSGI
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)

