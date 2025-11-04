"""
Admin Panel for NSE FII/DII Data Collector
Web interface to monitor cronjob status and view data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from nse_fiidii_collector import NSEDataCollector
from nse_option_chain_collector import NSEOptionChainCollector
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


def get_next_run_time():
    """Calculate next scheduled run time"""
    now = datetime.now()
    current_time = now.time()
    target_time = datetime.strptime("17:00", "%H:%M").time()
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # Check if today is a weekday (Monday=0 to Friday=4)
    if current_weekday < 5:  # Monday to Friday
        # If current time is before 5 PM today, next run is today at 5 PM
        if current_time < target_time:
            next_run = datetime.combine(now.date(), target_time)
            return next_run
        else:
            # Today after 5 PM, find next weekday
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:  # Skip weekends
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, target_time)
            return next_run
    
    # Current day is weekend, find next Monday
    days_until_monday = (7 - current_weekday) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # If it's Sunday, next Monday is 1 day away
    
    next_date = now.date() + timedelta(days=days_until_monday)
    next_run = datetime.combine(next_date, target_time)
    
    return next_run


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


@app.route('/api/data')
@token_required
def api_data():
    """API endpoint to get collected data with pagination"""
    try:
        collector = NSEDataCollector()
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by date (newest first)
        records = list(collector.collection.find().sort("date", -1).skip(skip).limit(limit))
        
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

def get_option_chain_next_run_time():
    """Calculate next scheduled run time for option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:  # Skip weekends
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    # Valid intervals: 09:15, 09:18, 09:21, ..., 03:27, 03:30
    
    # Calculate total minutes from 09:15:00
    start_datetime = datetime.combine(now.date(), start_time)
    minutes_from_start = int((now - start_datetime).total_seconds() / 60)
    
    # Calculate which interval we're in (0 = 09:15, 1 = 09:18, 2 = 09:21, etc.)
    current_interval = minutes_from_start // 3
    
    # Calculate the next interval
    next_interval = current_interval + 1
    
    # Convert next interval back to time
    next_minutes_from_start = next_interval * 3
    next_total_minutes = 15 + next_minutes_from_start  # 15 minutes from hour 9 = 09:15
    
    # Convert to hour and minute
    next_hour = 9 + (next_total_minutes // 60)
    next_minute = next_total_minutes % 60
    
    # Check if we've exceeded 15:30 (03:30 PM)
    # 15:30 = 15 hours * 60 + 30 minutes = 930 minutes from midnight
    # 09:15 = 9 hours * 60 + 15 minutes = 555 minutes from midnight
    # Maximum intervals from 09:15: (930 - 555) / 3 = 125 intervals
    max_minutes_from_start = (15 * 60 + 30) - (9 * 60 + 15)  # 375 minutes = 125 intervals
    
    if next_minutes_from_start > max_minutes_from_start:
        # Market closed, go to next weekday 09:15
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    next_run = datetime.combine(now.date(), dt_time(next_hour, next_minute))
    return next_run


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


@app.route('/api/option-chain/data')
def api_option_chain_data():
    """API endpoint to get collected option chain data with pagination"""
    try:
        collector = NSEOptionChainCollector()
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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


# BankNifty Option Chain Endpoints

def get_banknifty_option_chain_next_run_time():
    """Calculate next scheduled run time for BankNifty option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    # Same logic as NIFTY option chain
    return get_option_chain_next_run_time()


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
    """API endpoint to get collected BankNifty option chain data with pagination"""
    try:
        collector = NSEBankNiftyOptionChainCollector()
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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


# Finnifty Option Chain Endpoints

def get_finnifty_option_chain_next_run_time():
    """Calculate next scheduled run time for Finnifty option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    # Same logic as NIFTY option chain
    return get_option_chain_next_run_time()


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
    """API endpoint to get collected Finnifty option chain data with pagination"""
    try:
        collector = NSEFinniftyOptionChainCollector()
        
        # Get pagination parameters
        page, limit = get_pagination_params()
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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


# MidcapNifty Option Chain Endpoints

def get_midcpnifty_option_chain_next_run_time():
    """Calculate next scheduled run time for MidcapNifty option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    # Same logic as NIFTY option chain
    return get_option_chain_next_run_time()


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
    """API endpoint to get collected MidcapNifty option chain data with pagination"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSEMidcapNiftyOptionChainCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).skip(skip).limit(limit))
        
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


# HDFC Bank Option Chain Endpoints

def get_hdfcbank_option_chain_next_run_time():
    """Calculate next scheduled run time for HDFC Bank option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# ICICI Bank Option Chain Endpoints

def get_icicibank_option_chain_next_run_time():
    """Calculate next scheduled run time for ICICI Bank option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# SBIN Option Chain Endpoints

def get_sbin_option_chain_next_run_time():
    """Calculate next scheduled run time for SBIN option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# Kotak Bank Option Chain Endpoints

def get_kotakbank_option_chain_next_run_time():
    """Calculate next scheduled run time for Kotak Bank option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# Axis Bank Option Chain Endpoints

def get_axisbank_option_chain_next_run_time():
    """Calculate next scheduled run time for Axis Bank option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# Bank of Baroda Option Chain Endpoints

def get_bankbaroda_option_chain_next_run_time():
    """Calculate next scheduled run time for Bank of Baroda option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# PNB Option Chain Endpoints

def get_pnb_option_chain_next_run_time():
    """Calculate next scheduled run time for PNB option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# CANBK Option Chain Endpoints

def get_canbk_option_chain_next_run_time():
    """Calculate next scheduled run time for CANBK option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# AUBANK Option Chain Endpoints

def get_aubank_option_chain_next_run_time():
    """Calculate next scheduled run time for AUBANK option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# INDUSINDBK Option Chain Endpoints

def get_indusindbk_option_chain_next_run_time():
    """Calculate next scheduled run time for INDUSINDBK option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# IDFCFIRSTB Option Chain Endpoints

def get_idfcfirstb_option_chain_next_run_time():
    """Calculate next scheduled run time for IDFCFIRSTB option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# FEDERALBNK Option Chain Endpoints

def get_federalbnk_option_chain_next_run_time():
    """Calculate next scheduled run time for FEDERALBNK option chain (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:15
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:15
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:15 to 03:30)
    # Calculate next 3-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 3) + 1) * 3
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:15
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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


# Top 20 Gainers Endpoints

def get_gainers_next_run_time():
    """Calculate next scheduled run time for gainers (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=days_until_monday)
        return next_run
    
    # If before market hours, return today at 09:15
    if current_time < start_time:
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
        return next_run
    
    # If after market hours, return next day at 09:15
    if current_time > end_time:
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=1)
        # If next day is Saturday, skip to Monday
        if next_run.weekday() >= 5:
            days_until_monday = 7 - next_run.weekday()
            next_run += timedelta(days=days_until_monday)
        return next_run
    
    # During market hours, return next 3-minute interval
    current_minute = now.minute
    # Round up to next 3-minute interval
    next_minute = ((current_minute // 3) + 1) * 3
    if next_minute >= 60:
        next_hour = now.hour + 1
        next_minute = 0
        # Check if next hour is after market close
        if next_hour > end_time.hour or (next_hour == end_time.hour and next_minute > end_time.minute):
            # Return next day at 09:15
            next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=1)
            if next_run.weekday() >= 5:
                days_until_monday = 7 - next_run.weekday()
                next_run += timedelta(days=days_until_monday)
            return next_run
        next_run = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
    else:
        next_run = now.replace(minute=next_minute, second=0, microsecond=0)
    
    return next_run


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
    """API endpoint to get collected gainers data"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSEGainersCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("timestamp", -1).skip(skip).limit(limit))
        
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


# Top 20 Losers Endpoints

def get_losers_next_run_time():
    """Calculate next scheduled run time for losers (09:15 AM to 03:30 PM, every 3 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 15)  # 09:15 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:15
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=days_until_monday)
        return next_run
    
    # If before market hours, return today at 09:15
    if current_time < start_time:
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0)
        return next_run
    
    # If after market hours, return next day at 09:15
    if current_time > end_time:
        next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=1)
        # If next day is Saturday, skip to Monday
        if next_run.weekday() >= 5:
            days_until_monday = 7 - next_run.weekday()
            next_run += timedelta(days=days_until_monday)
        return next_run
    
    # During market hours, return next 3-minute interval
    current_minute = now.minute
    # Round up to next 3-minute interval
    next_minute = ((current_minute // 3) + 1) * 3
    if next_minute >= 60:
        next_hour = now.hour + 1
        next_minute = 0
        # Check if next hour is after market close
        if next_hour > end_time.hour or (next_hour == end_time.hour and next_minute > end_time.minute):
            # Return next day at 09:15
            next_run = now.replace(hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0) + timedelta(days=1)
            if next_run.weekday() >= 5:
                days_until_monday = 7 - next_run.weekday()
                next_run += timedelta(days=days_until_monday)
            return next_run
        next_run = now.replace(hour=next_hour, minute=next_minute, second=0, microsecond=0)
    else:
        next_run = now.replace(minute=next_minute, second=0, microsecond=0)
    
    return next_run


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
    """API endpoint to get collected losers data"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSELosersCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("timestamp", -1).skip(skip).limit(limit))
        
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


# News Collector Endpoints

def get_news_collector_next_run_time():
    """Calculate next scheduled run time for news collector (09:00 AM to 03:30 PM, every 15 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(9, 0)   # 09:00 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 09:00
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 09:00
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 09:00
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (09:00 to 03:30)
    # Calculate next 15-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 15) + 1) * 15
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:00
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 09:00
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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
    """API endpoint to get collected news data"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSENewsCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by pub_date (newest first)
        records = list(collector.collection.find().sort("pub_date", -1).skip(skip).limit(limit))
        
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


# Twitter collector endpoints removed - not needed


# ==================== LiveMint News Collector Endpoints ====================

def get_livemint_news_collector_next_run_time():
    """Calculate next scheduled run time for LiveMint news collector (07:00 AM to 03:30 PM, every 15 minutes)"""
    now = datetime.now()
    current_time = now.time()
    start_time = dt_time(7, 0)   # 07:00 AM
    end_time = dt_time(15, 30)   # 03:30 PM
    
    # Get current day of week (0 = Monday, 6 = Sunday)
    current_weekday = now.weekday()
    
    # If it's a weekend, return next Monday 07:00
    if current_weekday >= 5:  # Saturday or Sunday
        days_until_monday = (7 - current_weekday) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_date = now.date() + timedelta(days=days_until_monday)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # If before market opens today, return today 07:00
    if current_time < start_time:
        next_run = datetime.combine(now.date(), start_time)
        return next_run
    
    # If after market closes today, return next weekday 07:00
    if current_time > end_time:
        days_ahead = 1
        while (current_weekday + days_ahead) % 7 >= 5:
            days_ahead += 1
        next_date = now.date() + timedelta(days=days_ahead)
        next_run = datetime.combine(next_date, start_time)
        return next_run
    
    # We're within market hours (07:00 to 03:30)
    # Calculate next 15-minute interval
    current_minute = now.minute
    next_minute = ((current_minute // 15) + 1) * 15
    
    if next_minute >= 60:
        # Move to next hour
        next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        if next_time.time() > end_time:
            # After market close, go to next weekday 07:00
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time
    else:
        next_time = now.replace(minute=next_minute, second=0, microsecond=0)
        if next_time.time() > end_time:
            # After market close, go to next weekday 07:00
            days_ahead = 1
            while (current_weekday + days_ahead) % 7 >= 5:
                days_ahead += 1
            next_date = now.date() + timedelta(days=days_ahead)
            next_run = datetime.combine(next_date, start_time)
            return next_run
        return next_time


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
    """API endpoint to get collected LiveMint news data"""
    try:
        page, limit = get_pagination_params()
        skip = (page - 1) * limit
        
        collector = NSELiveMintNewsCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        
        # Get paginated records sorted by pub_date (newest first)
        records = list(collector.collection.find().sort("pub_date", -1).skip(skip).limit(limit))
        
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
    app.run(debug=True, host='0.0.0.0', port=5000)

