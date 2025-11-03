"""
Cronjob Scheduler for NSE FII/DII Data Collector
Runs Monday to Friday at 5:00 PM (17:00)
"""

import schedule
import time
import logging
from nse_fiidii_collector import NSEDataCollector
from datetime import datetime
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


STATUS_FILE = 'scheduler_status.json'

def run_collector():
    """Execute the NSE data collector"""
    collector = None
    try:
        # Cronjob triggered at {datetime.now()}
        
        collector = NSEDataCollector()
        success = collector.collect_and_save()
        
        if not success:
            logger.error("Cronjob completed with errors")
        
        # Update status file
        status_data = {
            "last_run": datetime.now().isoformat(),
            "last_status": "success" if success else "failed"
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
            
    except Exception as e:
        logger.error(f"Cronjob failed with error: {str(e)}")
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


def main():
    """Setup and run the scheduler"""
    # Starting NSE FII/DII Data Collector Scheduler
    # Schedule: Monday to Friday at 5:00 PM (17:00)
    
    # Schedule job for Monday to Friday at 5:00 PM
    schedule.every().monday.at("17:00").do(run_collector)
    schedule.every().tuesday.at("17:00").do(run_collector)
    schedule.every().wednesday.at("17:00").do(run_collector)
    schedule.every().thursday.at("17:00").do(run_collector)
    schedule.every().friday.at("17:00").do(run_collector)
    
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

