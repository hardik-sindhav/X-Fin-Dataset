"""
Cronjob Scheduler for NSE AUBANK Option Chain Data Collector
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 3 minutes
"""

import schedule
import time
import threading
import logging
from nse_aubank_option_chain_collector import NSEAUBANKOptionChainCollector
from datetime import datetime, time as dt_time, timedelta, date, timezone
from scheduler_config import get_config_for_scheduler, is_holiday
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aubank_option_chain_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
def get_scheduler_config():
    """Get scheduler configuration from config file"""
    config = get_config_for_scheduler("banks")
    if config:
        return config
    # Fallback to defaults
    return {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    }

STATUS_FILE = 'aubank_option_chain_scheduler_status.json'

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
    """Execute the collector"""
    global last_run_time
    
    # Check if already running (non-blocking check)
    if not execution_lock.acquire(blocking=False):
        logger.debug("Collector is already running, skipping this execution")
        return
    
    # Check minimum interval
    now = datetime.now(timezone.utc)
    config = get_scheduler_config()
    interval_minutes = config.get("interval_minutes", 3)
    min_interval_seconds = interval_minutes * 60 - 10  # Allow 10 seconds buffer
    
    collector = None
    lock_acquired = True
    try:
        if last_run_time:
            time_since_last_run = (now - last_run_time).total_seconds()
            if time_since_last_run < min_interval_seconds:
                logger.info(f"Skipping execution - only {time_since_last_run:.1f}s since last run (min {min_interval_seconds}s)")
                return
        
        # Check if it's market hours before running
        if not is_market_hours(now):
            logger.info(f"Outside market hours. Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        logger.info("=" * 60)
        logger.info(f"AUBANK Option Chain Cronjob triggered at {now}")
        
        logger.info("=" * 60)
        
        last_run_time = now
        
        collector = NSEAUBANKOptionChainCollector()
        success = collector.collect_and_save()
        
        if success:
            logger.info("AUBANK Option Chain Cronjob completed successfully")
        else:
            logger.error("AUBANK Option Chain Cronjob completed with errors")
        
        # Update status file
        status_data = {
            "last_run": now.isoformat(),
            "last_status": "success" if success else "failed"
        }
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(status_data, f)
        except Exception as e:
            logger.warning(f"Failed to update status file: {str(e)}")
            
    except Exception as e:
        logger.error(f"AUBANK Option Chain Cronjob failed with error: {str(e)}")
        # Update status file with error
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "error"
        }
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(status_data, f)
        except:
            pass
    finally:
        if collector:
            collector.close()
        if lock_acquired:
            execution_lock.release()
        logger.info("=" * 60)


def main():
    """Setup and run the scheduler"""
    config = get_scheduler_config()
    interval = config.get("interval_minutes", 3)
    start_time = config.get("start_time", "09:15")
    end_time = config.get("end_time", "15:30")
    enabled = config.get("enabled", True)
    
    logger.info("Starting scheduler")
    logger.info(f"Schedule: Monday to Friday from {start_time} to {end_time}, every {interval} minutes")
    logger.info(f"Enabled: {enabled}")
    
    if not enabled:
        logger.warning("Scheduler is disabled in configuration")
        return
    
    # Schedule job to run at specified interval
    # We'll check market hours and holidays inside the run_collector function
    schedule.every(interval).minutes.do(run_collector)
    
    logger.info("Scheduler configured. Waiting for scheduled times...")
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            # Sleep for 10 seconds for better timing accuracy
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


if __name__ == "__main__":
    main()

