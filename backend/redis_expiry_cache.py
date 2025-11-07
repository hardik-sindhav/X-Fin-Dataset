"""
Redis cache for NSE expiry dates
Caches expiry dates per day to avoid repeated API calls
"""

import redis
import logging
import os
from datetime import datetime, date
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Redis Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis key prefix for expiry dates
EXPIRY_KEY_PREFIX = "nse:expiry:"
EXPIRY_DATE_KEY_PREFIX = "nse:expiry_date:"


class RedisExpiryCache:
    """Redis cache for storing expiry dates with daily expiration"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.client = None
        self._connect_redis()
    
    def _connect_redis(self):
        """Establish Redis connection with error handling"""
        try:
            connection_params = {
                'host': REDIS_HOST,
                'port': REDIS_PORT,
                'db': REDIS_DB,
                'decode_responses': True,
                'socket_connect_timeout': 5,
                'socket_timeout': 5
            }
            
            if REDIS_PASSWORD:
                connection_params['password'] = REDIS_PASSWORD
            
            self.client = redis.Redis(**connection_params)
            # Test connection
            self.client.ping()
            logger.info(f"Successfully connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        except redis.ConnectionError as e:
            # Redis is optional - log as debug to reduce noise
            logger.debug(f"Redis not available at {REDIS_HOST}:{REDIS_PORT}: {str(e)}")
            logger.info("Redis connection unavailable. Expiry dates will be fetched from API each time.")
            self.client = None
        except Exception as e:
            # Only log unexpected errors as warnings
            logger.warning(f"Unexpected error connecting to Redis: {str(e)}")
            self.client = None
    
    def _get_today_key(self, symbol: str) -> str:
        """Get Redis key for today's expiry date for a symbol"""
        today = date.today().isoformat()
        return f"{EXPIRY_KEY_PREFIX}{symbol}:{today}"
    
    def _get_expiry_date_key(self, symbol: str) -> str:
        """Get Redis key for expiry date (without date suffix)"""
        return f"{EXPIRY_DATE_KEY_PREFIX}{symbol}"
    
    def get_expiry(self, symbol: str) -> Optional[str]:
        """
        Get cached expiry date for today
        Returns: Expiry date string (e.g., "25-Nov-2025") or None if not cached
        """
        if not self.client:
            return None
        
        try:
            # Check if we have expiry for today
            today_key = self._get_today_key(symbol)
            expiry = self.client.get(today_key)
            
            if expiry:
                logger.info(f"Found cached expiry for {symbol}: {expiry}")
                return expiry
            
            # Also check the general expiry date key (without date suffix)
            expiry_key = self._get_expiry_date_key(symbol)
            expiry = self.client.get(expiry_key)
            
            if expiry:
                # Verify it's still valid for today by checking the date stored
                stored_date = self.client.get(f"{expiry_key}:date")
                if stored_date and stored_date == date.today().isoformat():
                    logger.info(f"Found cached expiry for {symbol}: {expiry}")
                    return expiry
            
            logger.debug(f"No cached expiry found for {symbol} today")
            return None
            
        except redis.RedisError as e:
            logger.debug(f"Redis error getting expiry for {symbol}: {str(e)}")
            return None
        except Exception as e:
            logger.debug(f"Unexpected error getting expiry for {symbol}: {str(e)}")
            return None
    
    def set_expiry(self, symbol: str, expiry: str, ttl_seconds: int = None) -> bool:
        """
        Cache expiry date for today
        Args:
            symbol: Symbol name (e.g., "BANKNIFTY")
            expiry: Expiry date string (e.g., "25-Nov-2025")
            ttl_seconds: Time to live in seconds. If None, expires at end of day (default)
        Returns: True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            today = date.today()
            today_key = self._get_today_key(symbol)
            expiry_key = self._get_expiry_date_key(symbol)
            date_key = f"{expiry_key}:date"
            
            # Calculate TTL until end of day if not specified
            if ttl_seconds is None:
                now = datetime.now()
                end_of_day = datetime.combine(today, datetime.max.time())
                ttl_seconds = int((end_of_day - now).total_seconds()) + 60  # Add 1 minute buffer
            
            # Store expiry with today's date as key
            self.client.setex(today_key, ttl_seconds, expiry)
            
            # Also store in general key with date marker
            self.client.setex(expiry_key, ttl_seconds, expiry)
            self.client.setex(date_key, ttl_seconds, today.isoformat())
            
            logger.info(f"Cached expiry for {symbol}: {expiry} (TTL: {ttl_seconds}s)")
            return True
            
        except redis.RedisError as e:
            logger.debug(f"Redis error setting expiry for {symbol}: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error setting expiry for {symbol}: {str(e)}")
            return False
    
    def clear_expiry(self, symbol: str) -> bool:
        """
        Clear cached expiry date for a symbol
        Returns: True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            today_key = self._get_today_key(symbol)
            expiry_key = self._get_expiry_date_key(symbol)
            date_key = f"{expiry_key}:date"
            
            self.client.delete(today_key)
            self.client.delete(expiry_key)
            self.client.delete(date_key)
            
            logger.info(f"Cleared cached expiry for {symbol}")
            return True
            
        except redis.RedisError as e:
            logger.debug(f"Redis error clearing expiry for {symbol}: {str(e)}")
            return False
        except Exception as e:
            logger.debug(f"Unexpected error clearing expiry for {symbol}: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False


# Global instance
_expiry_cache = None

def get_expiry_cache() -> RedisExpiryCache:
    """Get global Redis expiry cache instance"""
    global _expiry_cache
    if _expiry_cache is None:
        _expiry_cache = RedisExpiryCache()
    return _expiry_cache

