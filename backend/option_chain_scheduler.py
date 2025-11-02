"""
Cronjob Scheduler for NSE Option Chain Data Collector
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 3 minutes
"""

import schedule
import time
import logging
from nse_option_chain_collector import NSEOptionChainCollector
from datetime import datetime, time as dt_time
import json
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('option_chain_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
START_TIME = dt_time(9, 15)  # 09:15 AM
END_TIME = dt_time(15, 30)   # 03:30 PM (15:30)
INTERVAL_MINUTES = 3

STATUS_FILE = 'option_chain_scheduler_status.json'


def is_market_hours(now: datetime) -> bool:
    """
    Check if current time is within market hours (09:15 AM to 03:30 PM)
    and if it's a weekday (Monday-Friday)
    """
    # Check if weekday (Monday=0 to Friday=4)
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    current_time = now.time()
    
    # Check if time is between 09:15 and 15:30
    if current_time < START_TIME or current_time > END_TIME:
        return False
    
    return True


def run_collector():
    """Execute the NSE option chain data collector"""
    collector = None
    try:
        now = datetime.now()
        
        # Check if it's market hours before running
        if not is_market_hours(now):
            logger.info(f"Outside market hours. Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            return
        
        logger.info("=" * 60)
        logger.info(f"Option Chain Cronjob triggered at {now}")
        logger.info("=" * 60)
        
        collector = NSEOptionChainCollector()
        success = collector.collect_and_save()
        
        if success:
            logger.info("Option Chain Cronjob completed successfully")
        else:
            logger.error("Option Chain Cronjob completed with errors")
        
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
        logger.error(f"Option Chain Cronjob failed with error: {str(e)}")
        # Update status file with error
        status_data = {
            "last_run": datetime.now().isoformat(),
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
        logger.info("=" * 60)


def main():
    """Setup and run the scheduler"""
    logger.info("Starting NSE Option Chain Data Collector Scheduler")
    logger.info(f"Schedule: Monday to Friday from {START_TIME.strftime('%H:%M')} to {END_TIME.strftime('%H:%M')}, every {INTERVAL_MINUTES} minutes")
    
    # Schedule job to run every 3 minutes during weekdays
    # We'll check market hours inside the run_collector function
    schedule.every(INTERVAL_MINUTES).minutes.do(run_collector)
    
    logger.info("Scheduler configured. Waiting for scheduled times...")
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            # Sleep for 1 minute to check for scheduled jobs
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Scheduler error: {str(e)}")


if __name__ == "__main__":
    main()

