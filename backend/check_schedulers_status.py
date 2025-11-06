#!/usr/bin/env python3
"""
Diagnostic script to check scheduler status on VPS
Run this on your VPS to see if schedulers are running
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_pm2_processes():
    """Check if PM2 is running and list processes"""
    print("\n" + "="*60)
    print("PM2 Process Status")
    print("="*60)
    try:
        result = subprocess.run(['pm2', 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout)
            
            # Check if backend is running
            if 'x-fin-backend' in result.stdout:
                print("\n✓ Backend process found in PM2")
            else:
                print("\n✗ Backend process NOT found in PM2")
                
            # Get PM2 logs
            print("\nRecent PM2 logs (last 20 lines):")
            try:
                log_result = subprocess.run(['pm2', 'logs', 'x-fin-backend', '--lines', '20', '--nostream'], 
                                           capture_output=True, text=True, timeout=10)
                if log_result.returncode == 0:
                    print(log_result.stdout)
                else:
                    print("Could not retrieve PM2 logs")
            except:
                print("Could not retrieve PM2 logs")
        else:
            print("PM2 command failed or PM2 not installed")
            print("Error:", result.stderr)
    except FileNotFoundError:
        print("PM2 is not installed or not in PATH")
    except Exception as e:
        print(f"Error checking PM2: {str(e)}")

def check_scheduler_status_files():
    """Check scheduler status files"""
    print("\n" + "="*60)
    print("Scheduler Status Files")
    print("="*60)
    
    status_files = [
        'scheduler_status.json',
        'option_chain_scheduler_status.json',
        'banknifty_option_chain_scheduler_status.json',
        'finnifty_option_chain_scheduler_status.json',
        'midcpnifty_option_chain_scheduler_status.json',
        'hdfcbank_option_chain_scheduler_status.json',
        'icicibank_option_chain_scheduler_status.json',
        'sbin_option_chain_scheduler_status.json',
        'kotakbank_option_chain_scheduler_status.json',
        'axisbank_option_chain_scheduler_status.json',
        'bankbaroda_option_chain_scheduler_status.json',
        'pnb_option_chain_scheduler_status.json',
        'canbk_option_chain_scheduler_status.json',
        'aubank_option_chain_scheduler_status.json',
        'indusindbk_option_chain_scheduler_status.json',
        'idfcfirstb_option_chain_scheduler_status.json',
        'federalbnk_option_chain_scheduler_status.json',
        'gainers_scheduler_status.json',
        'losers_scheduler_status.json',
        'news_collector_scheduler_status.json',
        'livemint_news_scheduler_status.json',
    ]
    
    found_count = 0
    for status_file in status_files:
        if os.path.exists(status_file):
            found_count += 1
            try:
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    last_run = data.get('last_run', 'Unknown')
                    status = data.get('last_status', 'Unknown')
                    print(f"✓ {status_file}")
                    print(f"  Last run: {last_run}")
                    print(f"  Status: {status}")
            except Exception as e:
                print(f"✗ {status_file} - Error reading: {str(e)}")
        else:
            print(f"✗ {status_file} - NOT FOUND")
    
    print(f"\nFound {found_count}/{len(status_files)} status files")

def check_python_processes():
    """Check if Python scheduler processes are running"""
    print("\n" + "="*60)
    print("Python Scheduler Processes")
    print("="*60)
    
    scheduler_keywords = [
        'cronjob_scheduler',
        'option_chain_scheduler',
        'banknifty_option_chain_scheduler',
        'finnifty_option_chain_scheduler',
        'midcpnifty_option_chain_scheduler',
        'hdfcbank_option_chain_scheduler',
        'icicibank_option_chain_scheduler',
        'sbin_option_chain_scheduler',
        'kotakbank_option_chain_scheduler',
        'axisbank_option_chain_scheduler',
        'bankbaroda_option_chain_scheduler',
        'pnb_option_chain_scheduler',
        'canbk_option_chain_scheduler',
        'aubank_option_chain_scheduler',
        'indusindbk_option_chain_scheduler',
        'idfcfirstb_option_chain_scheduler',
        'federalbnk_option_chain_scheduler',
        'gainers_scheduler',
        'losers_scheduler',
        'news_collector_scheduler',
        'livemint_news_scheduler',
        'admin_panel',
    ]
    
    try:
        # Use ps to find Python processes
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            found_processes = []
            
            for line in lines:
                for keyword in scheduler_keywords:
                    if keyword in line and 'python' in line.lower():
                        found_processes.append((keyword, line.strip()))
                        break
            
            if found_processes:
                print(f"Found {len(found_processes)} scheduler-related processes:")
                for keyword, process_line in found_processes:
                    print(f"  ✓ {keyword}: {process_line[:80]}...")
            else:
                print("✗ No scheduler processes found running")
                print("\nThis could mean:")
                print("  - Schedulers are not started")
                print("  - Schedulers crashed")
                print("  - Backend is not running")
        else:
            print("Could not check processes")
    except Exception as e:
        print(f"Error checking processes: {str(e)}")

def check_system_time():
    """Check system time and timezone"""
    print("\n" + "="*60)
    print("System Time & Timezone")
    print("="*60)
    
    try:
        # Check timedatectl
        result = subprocess.run(['timedatectl'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("Could not check timedatectl")
    except:
        print("Could not check system time")
    
    # Python time
    from datetime import datetime
    print(f"\nPython datetime.now(): {datetime.now()}")
    print(f"Python datetime.utcnow(): {datetime.utcnow()}")
    
    try:
        from timezone_utils import get_ist_now, get_utc_now
        print(f"IST time (timezone_utils): {get_ist_now()}")
        print(f"UTC time (timezone_utils): {get_utc_now()}")
    except ImportError:
        print("⚠ timezone_utils module not found (this is OK if not yet deployed)")

def check_config_file():
    """Check scheduler config file"""
    print("\n" + "="*60)
    print("Scheduler Configuration")
    print("="*60)
    
    config_file = 'scheduler_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                print(f"✓ Configuration file found: {config_file}")
                print("\nScheduler configurations:")
                for key, value in config.items():
                    if key != 'holidays':
                        print(f"\n{key}:")
                        for sub_key, sub_value in value.items():
                            print(f"  {sub_key}: {sub_value}")
                print(f"\nHolidays: {len(config.get('holidays', []))} configured")
        except Exception as e:
            print(f"✗ Error reading config: {str(e)}")
    else:
        print(f"✗ Configuration file NOT found: {config_file}")

def main():
    """Run all diagnostic checks"""
    print("="*60)
    print("SCHEDULER DIAGNOSTIC TOOL")
    print("="*60)
    print(f"Checked at: {datetime.now()}")
    
    # Change to backend directory if we're not already there
    if not os.path.exists('scheduler_config.json'):
        if os.path.exists('backend/scheduler_config.json'):
            os.chdir('backend')
            print("\nChanged to backend directory")
    
    check_system_time()
    check_pm2_processes()
    check_python_processes()
    check_config_file()
    check_scheduler_status_files()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC COMPLETE")
    print("="*60)
    print("\nRecommendations:")
    print("1. If PM2 backend is not running: pm2 start ecosystem.config.js")
    print("2. If schedulers are not found: Check backend logs in PM2")
    print("3. If time is wrong: Run fix-vps-time-and-cron.sh")
    print("4. If config file missing: It will be created automatically on first run")

if __name__ == "__main__":
    main()

