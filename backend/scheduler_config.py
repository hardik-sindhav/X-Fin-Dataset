"""
Scheduler Configuration Management
Handles configuration for all schedulers including intervals, start/end times, and holidays
"""

import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional

CONFIG_FILE = 'scheduler_config.json'

# Default configuration for all scheduler groups
DEFAULT_CONFIG = {
    "banks": {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    },
    "indices": {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    },
    "gainers_losers": {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    },
    "news": {
        "interval_minutes": 3,
        "start_time": "09:15",
        "end_time": "15:30",
        "enabled": True
    },
    "fiidii": {
        "interval_minutes": 60,
        "start_time": "17:00",
        "end_time": "17:00",
        "enabled": True
    },
    "holidays": []
}


def get_default_config() -> Dict:
    """Get default configuration"""
    return DEFAULT_CONFIG.copy()


def load_config() -> Dict:
    """Load configuration from file, create with defaults if not exists"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Merge with defaults to ensure all keys exist
            default = get_default_config()
            for key in default:
                if key not in config:
                    config[key] = default[key]
                elif key != "holidays" and isinstance(config[key], dict):
                    # Ensure all scheduler config keys exist
                    for sub_key in default[key]:
                        if sub_key not in config[key]:
                            config[key][sub_key] = default[key][sub_key]
            return config
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            return get_default_config()
    else:
        # Create default config file
        config = get_default_config()
        save_config(config)
        return config


def save_config(config: Dict) -> bool:
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def get_config_for_scheduler(scheduler_type: str) -> Optional[Dict]:
    """
    Get configuration for a specific scheduler type
    scheduler_type: 'banks', 'indices', 'gainers_losers', 'news', 'fiidii'
    """
    config = load_config()
    return config.get(scheduler_type)


def update_scheduler_config(scheduler_type: str, config_updates: Dict) -> bool:
    """Update configuration for a specific scheduler"""
    config = load_config()
    if scheduler_type in config and scheduler_type != "holidays":
        config[scheduler_type].update(config_updates)
        return save_config(config)
    return False


def get_holidays() -> List[str]:
    """Get list of holidays (as date strings YYYY-MM-DD)"""
    config = load_config()
    return config.get("holidays", [])


def add_holiday(holiday_date: str) -> bool:
    """Add a holiday (date string in YYYY-MM-DD format)"""
    config = load_config()
    holidays = config.get("holidays", [])
    
    # Validate date format
    try:
        datetime.strptime(holiday_date, "%Y-%m-%d")
    except ValueError:
        return False
    
    # Add if not already present
    if holiday_date not in holidays:
        holidays.append(holiday_date)
        holidays.sort()  # Keep sorted
        config["holidays"] = holidays
        return save_config(config)
    return True  # Already exists, consider success


def remove_holiday(holiday_date: str) -> bool:
    """Remove a holiday"""
    config = load_config()
    holidays = config.get("holidays", [])
    
    if holiday_date in holidays:
        holidays.remove(holiday_date)
        config["holidays"] = holidays
        return save_config(config)
    return True  # Not found, consider success


def is_holiday(check_date: Optional[date] = None) -> bool:
    """
    Check if a given date is a holiday
    If no date provided, checks today
    """
    if check_date is None:
        check_date = date.today()
    
    holidays = get_holidays()
    date_str = check_date.strftime("%Y-%m-%d")
    return date_str in holidays


def get_all_config() -> Dict:
    """Get complete configuration"""
    return load_config()

