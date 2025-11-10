"""
Cronjob Scheduler for NSE All Gainers and Losers Data Collector
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 3 minutes
Collects data for both gainers and losers in a single run
"""

import schedule
import time
import threading
from nse_all_gainers_losers_collector import NSEAllGainersLosersCollector, GAINERS_LOSERS
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
    config = get_config_for_scheduler("gainers_losers")
    if config:
        return config
    # Fallback to defaults
    return {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    }

STATUS_FILE = 'all_gainers_losers_scheduler_status.json'

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
    """Execute the collector for both gainers and losers"""
    global last_run_time
    
    if not execution_lock.acquire(blocking=False):
        logger.debug("All Gainers/Losers Collector is already running, skipping this execution")
        return
    
    now_ist = get_ist_now()
    config = get_scheduler_config()
    interval_minutes = config.get("interval_minutes", 3)
    min_interval_seconds = interval_minutes * 60 - 10
    
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
        logger.debug(f"All Gainers/Losers Cronjob triggered at {now_ist.strftime('%Y-%m-%d %H:%M:%S')} IST")
        logger.debug(f"Collecting data for {len(GAINERS_LOSERS)} types")
        logger.debug("=" * 60)
        
        last_run_time = now_ist
        collector = NSEAllGainersLosersCollector()
        results = collector.collect_and_save_all()  # This returns a dict of results per type
        
        # Count successes and failures
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        if successful == len(GAINERS_LOSERS):
            logger.debug(f"All Gainers/Losers Cronjob completed successfully - All {len(GAINERS_LOSERS)} types collected")
            overall_status = "success"
        elif successful > 0:
            logger.warning(f"All Gainers/Losers Cronjob completed with partial success - {successful}/{len(GAINERS_LOSERS)} types successful")
            overall_status = "partial"
        else:
            logger.error(f"All Gainers/Losers Cronjob completed with errors - All {len(GAINERS_LOSERS)} types failed")
            overall_status = "failed"
        
        # Log individual type results only if there are failures
        if failed > 0:
            for data_type, success in results.items():
                if not success:
                    display_name = next((c["display_name"] for c in GAINERS_LOSERS if c["type"] == data_type), data_type)
                    logger.warning(f"  ✗ {display_name}: Failed")
        
        # Update status file
        status_data = {
            "last_run": now_for_mongo().isoformat(),
            "last_status": overall_status,
            "successful": successful,
            "failed": failed,
            "total": len(GAINERS_LOSERS),
            "results": results
        }
        try:
            with open(STATUS_FILE, 'w') as f:
                json.dump(status_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to update status file: {str(e)}")
            
    except Exception as e:
        logger.error(f"All Gainers/Losers Cronjob failed with error: {str(e)}", exc_info=True)
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
    interval = config.get("interval_minutes", 3)
    start_time = config.get("start_time", "09:15")
    end_time = config.get("end_time", "15:30")
    enabled = config.get("enabled", True)
    
    logger.info("Starting All Gainers/Losers scheduler")
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
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            # Sleep for 10 seconds for better timing accuracy
            time.sleep(10)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()

