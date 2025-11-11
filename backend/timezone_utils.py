"""
Timezone Utility Module
Provides consistent timezone handling for IST (Asia/Kolkata)
All timestamps should use this module to ensure consistency
"""

from datetime import datetime
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC

def get_ist_now() -> datetime:
    """
    Get current datetime in IST timezone (Asia/Kolkata)
    Returns timezone-aware datetime object
    """
    return datetime.now(IST)

def get_utc_now() -> datetime:
    """
    Get current datetime in UTC timezone
    Returns timezone-aware datetime object
    """
    return datetime.now(UTC)

def utc_to_ist(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST
    """
    if utc_dt.tzinfo is None:
        # Assume naive datetime is UTC
        utc_dt = UTC.localize(utc_dt)
    return utc_dt.astimezone(IST)

def ist_to_utc(ist_dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC
    """
    if ist_dt.tzinfo is None:
        # Assume naive datetime is IST
        ist_dt = IST.localize(ist_dt)
    return ist_dt.astimezone(UTC)

def get_ist_now_naive() -> datetime:
    """
    Get current datetime in IST but as naive datetime (for MongoDB compatibility)
    MongoDB stores datetimes, and this returns a datetime that represents IST time
    but without timezone info (for backward compatibility)
    
    Uses UTC time and converts to IST for reliability, regardless of system timezone
    """
    # Get UTC time first, then convert to IST for reliability
    utc_now = datetime.now(UTC)
    ist_now = utc_now.astimezone(IST)
    # Return as naive datetime (IST time without timezone info)
    return ist_now.replace(tzinfo=None)

def get_utc_now_naive() -> datetime:
    """
    Get current UTC datetime as naive (for MongoDB compatibility)
    """
    return datetime.now(UTC).replace(tzinfo=None)

def now_for_mongo() -> datetime:
    """
    Get current datetime for MongoDB storage
    Uses IST time (Asia/Kolkata) to match local timezone
    Returns naive datetime in IST (stored as-is in MongoDB)
    """
    return get_ist_now_naive()

