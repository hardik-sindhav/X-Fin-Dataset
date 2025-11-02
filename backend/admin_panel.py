"""
Admin Panel for NSE FII/DII Data Collector
Web interface to monitor cronjob status and view data
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from nse_fiidii_collector import NSEDataCollector
from nse_option_chain_collector import NSEOptionChainCollector
from nse_banknifty_option_chain_collector import NSEBankNiftyOptionChainCollector
from nse_news_collector import NSENewsCollector
import schedule
import json
import os
from datetime import datetime, timedelta, time as dt_time
import threading
import time as time_module
import psutil
import sys

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

STATUS_FILE = 'scheduler_status.json'
OPTION_CHAIN_STATUS_FILE = 'option_chain_scheduler_status.json'
BANKNIFTY_STATUS_FILE = 'banknifty_option_chain_scheduler_status.json'
NEWS_COLLECTOR_STATUS_FILE = 'news_collector_scheduler_status.json'


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




@app.route('/api/status')
def api_status():
    """API endpoint to get scheduler status"""
    status = get_scheduler_status()
    return jsonify(status)


@app.route('/api/data')
def api_data():
    """API endpoint to get collected data"""
    try:
        collector = NSEDataCollector()
        
        # Get all records sorted by date (newest first)
        records = list(collector.collection.find().sort("date", -1))
        
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
        
        return jsonify({
            "success": True,
            "count": len(data),
            "data": data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/stats')
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
    """API endpoint to get collected option chain data"""
    try:
        collector = NSEOptionChainCollector()
        
        # Get all records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).limit(100))
        
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
        
        return jsonify({
            "success": True,
            "count": len(data),
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
    """API endpoint to get collected BankNifty option chain data"""
    try:
        collector = NSEBankNiftyOptionChainCollector()
        
        # Get all records sorted by timestamp (newest first)
        records = list(collector.collection.find().sort("records.timestamp", -1).limit(100))
        
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
        
        return jsonify({
            "success": True,
            "count": len(data),
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
def api_news_data():
    """API endpoint to get collected news data"""
    try:
        collector = NSENewsCollector()
        
        # Get all records sorted by pub_date (newest first)
        records = list(collector.collection.find().sort("pub_date", -1).limit(100))
        
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
        
        return jsonify({
            "success": True,
            "count": len(data),
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


if __name__ == '__main__':
    print("Starting Admin Panel...")
    print("Access the panel at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

