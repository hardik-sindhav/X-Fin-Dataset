"""
Cronjob Scheduler for NSE Top 20 Gainers Data Collector
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 10 minutes
Collects data for top 20 gainers
"""

import schedule
import time
import threading
from nse_all_gainers_losers_collector import NSEAllGainersLosersCollector
from datetime import datetime, time as dt_time, timedelta, date, timezone
from scheduler_config import get_config_for_scheduler, is_holiday
from timezone_utils import get_ist_now, now_for_mongo
from logger_config import get_logger
import json
import os

# Get logger
logger = get_logger(__name__)

# Load configuration
def get_scheduler_config():
    """Get scheduler configuration from config file"""
    config = get_config_for_scheduler("gainers")
    if config:
        return config
    # Fallback to defaults
    return {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    }

STATUS_FILE = 'gainers_scheduler_status.json'

# Execution lock to prevent concurrent runs
execution_lock = threading.Lock()
last_run_time = None


def is_market_hours(now: datetime) -> bool:
    """
    Check if current time is within market hours
    and if it's a weekday (Monday-Friday) and not a holiday
    """
    # Check if it's a holiday
    if is_holiday(now.date()):
        return False
    
    # Check if weekday (Monday=0 to Friday=4)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Get config
    config = get_scheduler_config()
    if not config.get("enabled", True):
        return False
    
    # Parse start and end times from config
    start_time_str = config.get("start_time", "09:15")
    end_time_str = config.get("end_time", "15:30")
    
    start_time = dt_time(*map(int, start_time_str.split(":")))
    end_time = dt_time(*map(int, end_time_str.split(":")))
    
    current_time = now.time()
    
    # Check if time is between start and end
    if current_time < start_time or current_time > end_time:
        return False
    
    return True


def run_collector():
    """Execute the collector for gainers"""
    global last_run_time
    
    # Check if already running (non-blocking check)
    if not execution_lock.acquire(blocking=False):
        logger.debug("Collector is already running, skipping this execution")
        return
    
    # Check minimum interval
    now_ist = get_ist_now()
    config = get_scheduler_config()
    interval_minutes = config.get("interval_minutes", 10)
    min_interval_seconds = interval_minutes * 60 - 10  # Allow 10 seconds buffer
    
    collector = None
    lock_acquired = True
    try:
        if last_run_time:
            time_since_last_run = (now_ist - last_run_time).total_seconds()
            if time_since_last_run < min_interval_seconds:
                logger.debug(f"Skipping execution - only {time_since_last_run:.1f}s since last run (min {min_interval_seconds}s)")
                lock_acquired = False
                return
        
        # Check if it's market hours before running
        if not is_market_hours(now_ist):
            logger.debug(f"Outside market hours. Current time: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")
            lock_acquired = False
            return
        
        logger.debug("=" * 60)
        logger.debug(f"Top 20 Gainers Cronjob triggered at {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")
        logger.debug("=" * 60)
        
        last_run_time = now_ist
        collector = None
        try:
            collector = NSEAllGainersLosersCollector()
            success = collector.collect_and_save_single("gainers")
            
            if success:
                logger.debug("Top 20 Gainers Cronjob completed successfully")
                overall_status = "success"
            else:
                logger.warning("Top 20 Gainers Cronjob completed with warnings (but continuing)")
                overall_status = "failed"
        except Exception as collector_error:
            logger.error(f"Error in collector (continuing): {str(collector_error)}", exc_info=True)
            success = False
            overall_status = "error"
            # Don't re-raise - let the scheduler continue
        
        # Update status file
        status_data = {
            "last_run": now_for_mongo().isoformat(),
            "last_status": overall_status,
            "success": success
        }
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update status file: {str(e)}")
            
    except Exception as e:
        logger.error(f"Top 20 Gainers Cronjob failed with error: {str(e)}", exc_info=True)
        # Update status file with error
        status_data = {
            "last_run": now_for_mongo().isoformat(),
            "last_status": "error",
            "error": str(e)
        }
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(status_data, f, indent=2)
        except:
            pass
    finally:
        if collector:
            collector.close()
        if lock_acquired:
            execution_lock.release()
        logger.debug("=" * 60)


def main():
    """Setup and run the scheduler"""
    config = get_scheduler_config()
    interval = config.get("interval_minutes", 10)
    start_time = config.get("start_time", "09:15")
    end_time = config.get("end_time", "15:30")
    enabled = config.get("enabled", True)
    
    logger.info("Starting NSE Top 20 Gainers Data Collector Scheduler")
    logger.debug(f"Schedule: Monday to Friday from {start_time} to {end_time}, every {interval} minutes")
    logger.debug(f"Enabled: {enabled}")
    
    if not enabled:
        logger.warning("Scheduler is disabled in configuration")
        return
    
    # Schedule job to run at specified interval
    # We'll check market hours and holidays inside the run_collector function
    schedule.every(interval).minutes.do(run_collector)
    
    logger.debug("Scheduler configured. Waiting for scheduled times...")
    
    # Run immediately if within market hours (for testing and immediate execution)
    now_ist = get_ist_now()
    if is_market_hours(now_ist):
        logger.debug(f"Market is open. Running collector immediately at {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")
        run_collector()
    
    # Keep the script running - never stop even on errors
    while True:
        try:
            schedule.run_pending()
            # Sleep for 10 seconds for better timing accuracy
            time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error (continuing): {str(e)}", exc_info=True)
            # Continue running even after errors - don't stop the scheduler
            time.sleep(10)


if __name__ == "__main__":
    main()

