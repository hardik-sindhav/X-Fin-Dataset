"""
Master Scheduler Script - Runs All Data Collectors Automatically
Starts all schedulers in separate threads to run concurrently
"""

import threading
import time
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('master_scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import all schedulers
SCHEDULERS = []

def start_scheduler(module_name, scheduler_name):
    """Start a scheduler in a separate thread"""
    try:
        logger.info(f"Starting {scheduler_name}...")
        module = __import__(module_name)
        # Each scheduler module has a run loop in its __main__ or we call it directly
        # Most schedulers run in an infinite loop, so we just need to run them
        
        # Check if module has a run or main function
        if hasattr(module, 'main'):
            module.main()
        elif hasattr(module, 'run'):
            module.run()
        else:
            # Execute the scheduler file
            import subprocess
            import os
            scheduler_file = f"{module_name}.py"
            if os.path.exists(scheduler_file):
                # Run the scheduler in a subprocess
                process = subprocess.Popen(
                    [sys.executable, scheduler_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.dirname(os.path.abspath(scheduler_file))
                )
                logger.info(f"{scheduler_name} started in subprocess (PID: {process.pid})")
                return process
            else:
                logger.error(f"Scheduler file not found: {scheduler_file}")
                return None
    except Exception as e:
        logger.error(f"Failed to start {scheduler_name}: {str(e)}")
        return None


def run_scheduler_in_thread(module_name, scheduler_name):
    """Run scheduler in a separate thread"""
    def scheduler_worker():
        try:
            # Thread started for {scheduler_name}
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


def main():
    """Start all schedulers"""
    # MASTER SCHEDULER - Starting All Data Collectors
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
    
    threads = []
    
    # Start each scheduler in a separate thread
    for module_name, scheduler_name in schedulers:
        thread = run_scheduler_in_thread(module_name, scheduler_name)
        threads.append((thread, scheduler_name))
        time.sleep(0.5)  # Small delay between starting schedulers
    
    # All {len(threads)} schedulers started successfully!
    
    # Keep main thread alive
    try:
        while True:
            # Check if all threads are still alive
            alive_count = sum(1 for thread, name in threads if thread.is_alive())
            if alive_count < len(threads):
                logger.warning(f"Some schedulers stopped. Alive: {alive_count}/{len(threads)}")
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        pass  # Stopping all schedulers...


if __name__ == '__main__':
    main()

