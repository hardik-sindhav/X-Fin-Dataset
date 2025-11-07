"""
Cronjob Scheduler for NSE FII/DII Data Collector
Runs Monday to Friday at 5:00 PM (17:00)
"""

import schedule
import time
import logging
from nse_fiidii_collector import NSEDataCollector
from datetime import datetime, date, timezone
from scheduler_config import get_config_for_scheduler, is_holiday
import json
import os

# Configure logging - Only show warnings and errors
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console only - no individual log files
    ]
)
logger = logging.getLogger(__name__)

# Load configuration
def get_scheduler_config():
    """Get scheduler configuration from config file"""
    config = get_config_for_scheduler("fiidii")
    if config:
        return config
    # Fallback to defaults
    return {
        "interval_minutes": 60,
        "start_time": "17:00",
        "end_time": "17:00",
        "enabled": True
    }

STATUS_FILE = 'scheduler_status.json'

def run_collector():
    """Execute the NSE data collector"""
    # Check if it's a holiday
    now = datetime.now(timezone.utc)
    if is_holiday(now.date()):
        logger.info(f"Skipping FII/DII collection - holiday: {now.strftime('%Y-%m-%d')}")
        return
    
    # Check if weekday (Monday=0 to Friday=4)
    if now.weekday() >= 5:  # Saturday or Sunday
        return
    
    # Check if enabled
    config = get_scheduler_config()
    if not config.get("enabled", True):
        return
    
    collector = None
    try:
        logger.info(f"FII/DII Cronjob triggered at {now}")
        
        collector = NSEDataCollector()
        success = collector.collect_and_save()
        
        if not success:
            logger.error("Cronjob completed with errors")
        
        # Update status file
        status_data = {
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_status": "success" if success else "failed"
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
            
    except Exception as e:
        logger.error(f"Cronjob failed with error: {str(e)}")
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


def main():
    """Setup and run the scheduler"""
    config = get_scheduler_config()
    start_time = config.get("start_time", "17:00")
    enabled = config.get("enabled", True)
    
    logger.info("Starting NSE FII/DII Data Collector Scheduler")
    logger.info(f"Schedule: Monday to Friday at {start_time}")
    logger.info(f"Enabled: {enabled}")
    
    if not enabled:
        logger.warning("Scheduler is disabled in configuration")
        return
    
    # Schedule job for Monday to Friday at configured time
    schedule.every().monday.at(start_time).do(run_collector)
    schedule.every().tuesday.at(start_time).do(run_collector)
    schedule.every().wednesday.at(start_time).do(run_collector)
    schedule.every().thursday.at(start_time).do(run_collector)
    schedule.every().friday.at(start_time).do(run_collector)
    
    # Scheduler configured. Waiting for scheduled time...
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        pass  # Scheduler stopped by user
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


if __name__ == "__main__":
    main()

