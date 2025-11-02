"""
NSE INDUSINDBK (IndusInd Bank) Option Chain Data Collector
Collects data from NSE API and stores in MongoDB
Runs Monday to Friday from 09:15 AM to 03:30 PM, every 3 minutes
"""

import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime
import time
import logging
from typing import Optional, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('indusindbk_option_chain_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
EXPIRY_API_URL = "https://www.nseindia.com/api/option-chain-contract-info?symbol=INDUSINDBK"
OPTION_CHAIN_API_URL = "https://www.nseindia.com/api/option-chain-v3"
SYMBOL = "INDUSINDBK"
TYPE = "Equity"  # Use Equity type for stocks
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_INDUSINDBK_OPTION_CHAIN_COLLECTION_NAME', 'indusindbk_option_chain_data')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)


class NSEIndusIndBkOptionChainCollector:
    """Collects and stores NSE INDUSINDBK Option Chain data in MongoDB"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.collection = None
        self._connect_mongo()
    
    def _connect_mongo(self):
        """Establish MongoDB connection with error handling"""
        try:
            if MONGO_USERNAME and MONGO_PASSWORD:
                mongo_uri = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
            else:
                mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
            
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[MONGO_DB_NAME]
            self.collection = self.db[MONGO_COLLECTION_NAME]
            
            # Create unique index on timestamp to prevent duplicates
            self.collection.create_index([("records.timestamp", 1)], unique=True)
            
            logger.info(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
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
    
    def _fetch_expiry_dates_with_retry(self) -> Optional[str]:
        """
        Fetch expiry dates from NSE API with retry logic
        Returns: First expiry date string (e.g., "25-Nov-2025") or None if all retries fail
        """
        headers = self._get_headers()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching expiry dates for {SYMBOL} (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(EXPIRY_API_URL, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract expiry dates
                expiry_dates = data.get("expiryDates", [])
                
                if not expiry_dates or not isinstance(expiry_dates, list):
                    logger.error(f"Unexpected expiry dates format: {type(expiry_dates)}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                if len(expiry_dates) == 0:
                    logger.error("No expiry dates found in response")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Always pick the first expiry date
                first_expiry = expiry_dates[0]
                logger.info(f"Successfully fetched expiry dates. Using first expiry: {first_expiry}")
                return first_expiry
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for expiry dates")
                    
            except Exception as e:
                logger.error(f"Unexpected error (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for expiry dates")
        
        return None
    
    def _fetch_option_chain_with_retry(self, expiry_date: str) -> Optional[Dict]:
        """
        Fetch option chain data from NSE API with retry logic
        Args:
            expiry_date: Expiry date string (e.g., "25-Nov-2025")
        Returns: Full API response as dict or None if all retries fail
        """
        headers = self._get_headers()
        url = f"{OPTION_CHAIN_API_URL}?type={TYPE}&symbol={SYMBOL}&expiry={expiry_date}"
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching option chain data for {SYMBOL} expiry {expiry_date} (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.error(f"Unexpected data format: {type(data)}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Check if timestamp exists in the response
                records = data.get("records", {})
                timestamp = records.get("timestamp") if isinstance(records, dict) else None
                
                if not timestamp:
                    logger.error("Timestamp not found in option chain response")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.info(f"Successfully fetched option chain data. Timestamp: {timestamp}")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for option chain data")
                    
            except Exception as e:
                logger.error(f"Unexpected error (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for option chain data")
        
        return None
    
    def _save_to_mongo(self, data: Dict) -> bool:
        """
        Save entire option chain response to MongoDB
        Uses timestamp field as unique identifier to prevent duplicates
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning("No data to save")
            return False
        
        try:
            # Extract timestamp for duplicate check
            records = data.get("records", {})
            timestamp = records.get("timestamp") if isinstance(records, dict) else None
            
            if not timestamp:
                logger.error("Cannot save: timestamp not found in data")
                return False
            
            # Use upsert with timestamp as unique identifier
            result = self.collection.update_one(
                {"records.timestamp": timestamp},
                {
                    "$set": {
                        **data,
                        "updatedAt": datetime.utcnow()
                    },
                    "$setOnInsert": {
                        "insertedAt": datetime.utcnow()
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"Inserted new record with timestamp: {timestamp}")
                return True
            elif result.modified_count > 0:
                logger.info(f"Updated existing record with timestamp: {timestamp}")
                return True
            else:
                logger.debug(f"Record with timestamp {timestamp} already exists (no changes)")
                return True  # Still considered successful if no duplicates
                
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"Duplicate record skipped for timestamp: {timestamp}")
            return True  # Duplicate prevention working correctly
            
        except Exception as e:
            logger.error(f"Failed to save data to MongoDB: {str(e)}")
            return False
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect option chain data and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info(f"Starting NSE {SYMBOL} option chain data collection...")
            
            # Step 1: Fetch expiry dates and pick the first one
            expiry_date = self._fetch_expiry_dates_with_retry()
            
            if not expiry_date:
                logger.error("Failed to fetch expiry dates after all retries")
                return False
            
            # Step 2: Fetch option chain data using the first expiry date
            option_chain_data = self._fetch_option_chain_with_retry(expiry_date)
            
            if option_chain_data is None:
                logger.error("Failed to fetch option chain data after all retries")
                return False
            
            # Step 3: Save entire response to MongoDB
            success = self._save_to_mongo(option_chain_data)
            
            if success:
                logger.info(f"NSE {SYMBOL} option chain data collection completed successfully")
            else:
                logger.error("Failed to save option chain data to MongoDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in collect_and_save: {str(e)}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def main():
    """Main execution function"""
    collector = None
    try:
        collector = NSEIndusIndBkOptionChainCollector()
        success = collector.collect_and_save()
        exit_code = 0 if success else 1
        exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        exit(1)
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()

