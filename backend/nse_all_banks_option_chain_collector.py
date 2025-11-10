"""
NSE All Banks Option Chain Data Collector
Collects data from NSE API for all 12 banks and stores in MongoDB
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 3 minutes
"""

import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime
import time
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv
from redis_expiry_cache import get_expiry_cache
from urllib.parse import quote_plus
from timezone_utils import now_for_mongo
from logger_config import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger(__name__)

# Configuration
OPTION_CHAIN_API_URL = "https://www.nseindia.com/api/option-chain-v3"
TYPE = "Equity"  # Use Equity type for stocks
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# List of all 12 banks to collect
BANKS = [
    {"symbol": "HDFCBANK", "collection": "hdfcbank_option_chain_data"},
    {"symbol": "ICICIBANK", "collection": "icicibank_option_chain_data"},
    {"symbol": "SBIN", "collection": "sbin_option_chain_data"},
    {"symbol": "KOTAKBANK", "collection": "kotakbank_option_chain_data"},
    {"symbol": "AXISBANK", "collection": "axisbank_option_chain_data"},
    {"symbol": "BANKBARODA", "collection": "bankbaroda_option_chain_data"},
    {"symbol": "PNB", "collection": "pnb_option_chain_data"},
    {"symbol": "CANBK", "collection": "canbk_option_chain_data"},
    {"symbol": "AUBANK", "collection": "aubank_option_chain_data"},
    {"symbol": "INDUSINDBK", "collection": "indusindbk_option_chain_data"},
    {"symbol": "IDFCFIRSTB", "collection": "idfcfirstb_option_chain_data"},
    {"symbol": "FEDERALBNK", "collection": "federalbnk_option_chain_data"},
]

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)


class NSEAllBanksOptionChainCollector:
    """Collects and stores NSE Option Chain data for all banks in MongoDB"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.collections = {}  # Store collection references for each bank
        self.expiry_cache = get_expiry_cache()
        self._connect_mongo()
    
    def _connect_mongo(self):
        """Establish MongoDB connection with error handling"""
        try:
            if MONGO_USERNAME and MONGO_PASSWORD:
                # URL-encode username and password to handle special characters like @, :, etc.
                encoded_username = quote_plus(MONGO_USERNAME)
                encoded_password = quote_plus(MONGO_PASSWORD)
                # Get auth source (default to 'admin' for MongoDB) - REQUIRED for authentication
                MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
                # Build connection string with authSource parameter (required for MongoDB auth)
                mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
            else:
                mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
            
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[MONGO_DB_NAME]
            
            # Create collection references for all banks
            for bank in BANKS:
                collection_name = os.getenv(
                    f'MONGO_{bank["symbol"]}_OPTION_CHAIN_COLLECTION_NAME',
                    bank["collection"]
                )
                collection = self.db[collection_name]
                # Create unique index on timestamp to prevent duplicates
                collection.create_index([("records.timestamp", 1)], unique=True)
                self.collections[bank["symbol"]] = collection
            
            logger.debug(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
            logger.debug(f"Initialized collections for {len(BANKS)} banks")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for NSE API requests"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
            'Origin': 'https://www.nseindia.com'
        }
    
    def _fetch_expiry_dates_with_retry(self, symbol: str) -> Optional[str]:
        """
        Fetch expiry dates from NSE API with retry logic
        First checks Redis cache, then fetches from API if not cached
        Returns: First expiry date string (e.g., "25-Nov-2025") or None if all retries fail
        """
        # First, try to get from Redis cache
        cached_expiry = self.expiry_cache.get_expiry(symbol)
        if cached_expiry:
            logger.debug(f"Using cached {symbol} expiry date: {cached_expiry}")
            return cached_expiry
        
        # If not in cache, fetch from API
        expiry_api_url = f"https://www.nseindia.com/api/option-chain-contract-info?symbol={symbol}"
        headers = self._get_headers()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Fetching expiry dates for {symbol} from API (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(expiry_api_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract expiry dates
                expiry_dates = data.get("expiryDates", [])
                
                if not expiry_dates or not isinstance(expiry_dates, list) or len(expiry_dates) == 0:
                    logger.warning(f"No expiry dates found for {symbol}")
                    if attempt < MAX_RETRIES:
                        logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Always pick the first expiry date
                first_expiry = expiry_dates[0]
                logger.debug(f"Successfully fetched {symbol} expiry dates. Using first expiry: {first_expiry}")
                
                # Cache the expiry date for today
                try:
                    self.expiry_cache.set_expiry(symbol, first_expiry)
                except Exception as cache_error:
                    logger.warning(f"Failed to cache expiry date for {symbol}: {str(cache_error)}")
                    # Continue even if caching fails
                
                return first_expiry
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {symbol} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {symbol} expiry dates")
                    
            except Exception as e:
                logger.warning(f"Unexpected error for {symbol} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {symbol} expiry dates")
        
        return None
    
    def _fetch_option_chain_with_retry(self, symbol: str, expiry_date: str) -> Optional[Dict]:
        """
        Fetch option chain data from NSE API with retry logic
        Args:
            symbol: Bank symbol (e.g., "HDFCBANK")
            expiry_date: Expiry date string (e.g., "25-Nov-2025")
        Returns: Full API response as dict or None if all retries fail
        """
        headers = self._get_headers()
        url = f"{OPTION_CHAIN_API_URL}?type={TYPE}&symbol={symbol}&expiry={expiry_date}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Fetching option chain data for {symbol} expiry {expiry_date} (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.warning(f"Unexpected data format for {symbol}: {type(data)}")
                    if attempt < MAX_RETRIES:
                        logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Check if timestamp exists in the response
                records = data.get("records", {})
                timestamp = records.get("timestamp") if isinstance(records, dict) else None
                
                if not timestamp:
                    logger.warning(f"Timestamp not found in option chain response for {symbol}")
                    if attempt < MAX_RETRIES:
                        logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.debug(f"Successfully fetched option chain data for {symbol}. Timestamp: {timestamp}")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {symbol} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {symbol} option chain data")
                    
            except Exception as e:
                logger.warning(f"Unexpected error for {symbol} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {symbol} option chain data")
        
        return None
    
    def _save_to_mongo(self, symbol: str, data: Dict) -> bool:
        """
        Save entire option chain response to MongoDB for a specific bank
        Uses timestamp field as unique identifier to prevent duplicates
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning(f"No data to save for {symbol}")
            return False
        
        try:
            collection = self.collections.get(symbol)
            if collection is None:
                logger.error(f"Collection not found for {symbol}")
                return False
            
            # Extract timestamp for duplicate check
            records = data.get("records", {})
            timestamp = records.get("timestamp") if isinstance(records, dict) else None
            
            if not timestamp:
                logger.error(f"Cannot save {symbol}: timestamp not found in data")
                return False
            
            # Use upsert with timestamp as unique identifier
            result = collection.update_one(
                {"records.timestamp": timestamp},
                {
                    "$set": {
                        **data,
                        "updatedAt": now_for_mongo()
                    },
                    "$setOnInsert": {
                        "insertedAt": now_for_mongo()
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Inserted new record for {symbol} with timestamp: {timestamp}")
                return True
            elif result.modified_count > 0:
                logger.debug(f"Updated existing record for {symbol} with timestamp: {timestamp}")
                return True
            else:
                logger.debug(f"Record for {symbol} with timestamp {timestamp} already exists (no changes)")
                return True  # Still considered successful if no duplicates
                
        except pymongo.errors.DuplicateKeyError:
            logger.debug(f"Duplicate record skipped for {symbol} timestamp: {timestamp}")
            return True  # Duplicate prevention working correctly
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to save {symbol} data to MongoDB: {error_msg}")
            return False
    
    def collect_and_save_single_bank(self, bank: Dict) -> bool:
        """
        Collect option chain data for a single bank and save to MongoDB
        Args:
            bank: Bank dictionary with 'symbol' and 'collection' keys
        Returns: True if successful, False otherwise
        """
        symbol = bank["symbol"]
        try:
            logger.debug(f"Starting NSE {symbol} option chain data collection...")
            
            # Step 1: Fetch expiry dates and pick the first one
            expiry_date = self._fetch_expiry_dates_with_retry(symbol)
            
            if not expiry_date:
                logger.error(f"Failed to fetch expiry dates for {symbol} after all retries")
                return False
            
            # Step 2: Fetch option chain data using the first expiry date
            option_chain_data = self._fetch_option_chain_with_retry(symbol, expiry_date)
            
            if option_chain_data is None:
                logger.error(f"Failed to fetch option chain data for {symbol} after all retries")
                return False
            
            # Step 3: Save entire response to MongoDB
            success = self._save_to_mongo(symbol, option_chain_data)
            
            if success:
                logger.debug(f"NSE {symbol} option chain data collection completed successfully")
            else:
                logger.warning(f"Failed to save {symbol} option chain data to MongoDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in collect_and_save_single_bank for {symbol}: {str(e)}", exc_info=True)
            return False
    
    def collect_and_save_all_banks(self) -> Dict[str, bool]:
        """
        Main method to collect option chain data for all banks and save to MongoDB
        Returns: Dictionary mapping bank symbols to success status
        """
        results = {}
        logger.debug(f"Starting NSE All Banks Option Chain data collection for {len(BANKS)} banks...")
        
        for bank in BANKS:
            symbol = bank["symbol"]
            try:
                success = self.collect_and_save_single_bank(bank)
                results[symbol] = success
                
                # Small delay between banks to avoid overwhelming the API
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {str(e)}", exc_info=True)
                results[symbol] = False
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        
        if failed > 0:
            logger.warning(f"All Banks Option Chain collection completed: {successful} successful, {failed} failed")
        else:
            logger.debug(f"All Banks Option Chain collection completed: {successful} successful, {failed} failed")
        
        return results
    
    def get_collection(self, symbol: str):
        """
        Get MongoDB collection for a specific bank symbol
        Args:
            symbol: Bank symbol (e.g., "HDFCBANK")
        Returns: MongoDB collection object or None if not found
        """
        return self.collections.get(symbol)
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.debug("MongoDB connection closed")


def main():
    """Main execution function"""
    collector = None
    try:
        collector = NSEAllBanksOptionChainCollector()
        results = collector.collect_and_save_all_banks()
        
        # Exit with error code if any bank failed
        exit_code = 0 if all(results.values()) else 1
        exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1)
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()

