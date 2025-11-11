"""
NSE Gainers and Losers Data Collector
Collects data from NSE API for gainers and losers and stores in MongoDB
"""

import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime
import time
from typing import Optional, Dict
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from logger_config import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger(__name__)

# Configuration
GAINERS_API_URL = "https://www.nseindia.com/api/live-analysis-variations?index=gainers"
LOSERS_API_URL = "https://www.nseindia.com/api/live-analysis-variations?index=loosers"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)

# Collection names
MONGO_GAINERS_COLLECTION_NAME = os.getenv('MONGO_GAINERS_COLLECTION_NAME', 'gainers_data')
MONGO_LOSERS_COLLECTION_NAME = os.getenv('MONGO_LOSERS_COLLECTION_NAME', 'losers_data')


class NSEGainersLosersCollector:
    """Collects and stores NSE Gainers and Losers data in MongoDB"""
    
    def __init__(self):
        """Initialize MongoDB connection"""
        self.client = None
        self.db = None
        self.gainers_collection = None
        self.losers_collection = None
        self._connect_mongo()
    
    def _connect_mongo(self):
        """Establish MongoDB connection with error handling"""
        try:
            if MONGO_USERNAME and MONGO_PASSWORD:
                # URL-encode username and password to handle special characters
                encoded_username = quote_plus(MONGO_USERNAME)
                encoded_password = quote_plus(MONGO_PASSWORD)
                MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
                mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
            else:
                mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
            
            self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[MONGO_DB_NAME]
            
            # Initialize collections
            self.gainers_collection = self.db[MONGO_GAINERS_COLLECTION_NAME]
            self.losers_collection = self.db[MONGO_LOSERS_COLLECTION_NAME]
            
            # Create unique index on timestamp to prevent duplicates
            try:
                self.gainers_collection.create_index([("timestamp", 1)], unique=True)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.debug(f"Gainers index creation note: {str(e)}")
            
            try:
                self.losers_collection.create_index([("timestamp", 1)], unique=True)
            except Exception as e:
                if "already exists" not in str(e).lower():
                    logger.debug(f"Losers index creation note: {str(e)}")
            
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
    
    def _fetch_data_with_retry(self, api_url: str, data_type: str) -> Optional[Dict]:
        """
        Fetch data from NSE API with retry logic
        Args:
            api_url: API URL to fetch from
            data_type: Type of data ("gainers" or "losers")
        Returns: Full API response as dict or None if all retries fail
        """
        headers = self._get_headers()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching {data_type} data (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.error(f"Unexpected data format for {data_type}: {type(data)}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Check if we have at least one timestamp in the response
                timestamp = None
                for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                    if key in data and isinstance(data[key], dict):
                        section_timestamp = data[key].get('timestamp')
                        if section_timestamp:
                            timestamp = section_timestamp
                            break
                
                # Also check for top-level timestamp
                if not timestamp and 'timestamp' in data:
                    timestamp = data.get('timestamp')
                
                if not timestamp:
                    logger.error(f"Timestamp not found in {data_type} response. Available keys: {list(data.keys())[:10]}")
                    # Log first section structure for debugging
                    for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                        if key in data:
                            logger.debug(f"{key} section structure: {type(data[key])}, keys: {list(data[key].keys())[:5] if isinstance(data[key], dict) else 'N/A'}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.info(f"Successfully fetched {data_type} data. Timestamp: {timestamp}")
                
                # Add top-level timestamp for easier querying
                data['timestamp'] = timestamp
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {data_type} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {data_type} data")
                    
            except Exception as e:
                logger.error(f"Unexpected error for {data_type} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {data_type} data")
        
        return None
    
    def _save_to_mongo(self, data_type: str, data: Dict) -> bool:
        """
        Save entire response to MongoDB
        Uses timestamp field as unique identifier to prevent duplicates
        Args:
            data_type: Type of data ("gainers" or "losers")
            data: Data dictionary to save
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning(f"No data to save for {data_type}")
            return False
        
        try:
            # Select collection based on data type
            if data_type == "gainers":
                collection = self.gainers_collection
            elif data_type == "losers":
                collection = self.losers_collection
            else:
                logger.error(f"Invalid data type: {data_type}")
                return False
            
            # Extract timestamp for duplicate check
            timestamp = data.get('timestamp')
            if not timestamp:
                # Try to get timestamp from first available section
                for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                    if key in data and isinstance(data[key], dict):
                        section_timestamp = data[key].get('timestamp')
                        if section_timestamp:
                            timestamp = section_timestamp
                            data['timestamp'] = timestamp
                            break
            
            if not timestamp:
                logger.error(f"Cannot save {data_type}: timestamp not found in data. Data keys: {list(data.keys())[:10]}")
                # Log data structure for debugging
                logger.debug(f"Data structure sample: {str(data)[:500]}")
                return False
            
            # Use upsert with timestamp as unique identifier
            result = collection.update_one(
                {"timestamp": timestamp},
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
                logger.info(f"Inserted new {data_type} record with timestamp: {timestamp}")
                return True
            elif result.modified_count > 0:
                logger.info(f"Updated existing {data_type} record with timestamp: {timestamp}")
                return True
            else:
                logger.debug(f"{data_type.capitalize()} record with timestamp {timestamp} already exists (no changes)")
                return True
                
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"Duplicate {data_type} record skipped for timestamp: {timestamp}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save {data_type} data to MongoDB: {str(e)}")
            return False
    
    def collect_and_save_single(self, data_type: str) -> bool:
        """
        Collect and save data for a single type (gainers or losers)
        Args:
            data_type: Type of data ("gainers" or "losers")
        Returns: True if successful, False otherwise
        """
        try:
            if data_type == "gainers":
                api_url = GAINERS_API_URL
                display_name = "Top 20 Gainers"
            elif data_type == "losers":
                api_url = LOSERS_API_URL
                display_name = "Top 20 Losers"
            else:
                logger.error(f"Invalid data type: {data_type}")
                return False
            
            logger.info(f"Starting {display_name} data collection...")
            
            # Fetch data
            data = self._fetch_data_with_retry(api_url, data_type)
            
            if data is None:
                logger.error(f"Failed to fetch {display_name} data after all retries")
                return False
            
            # Save to MongoDB
            success = self._save_to_mongo(data_type, data)
            
            if success:
                logger.info(f"{display_name} data collection completed successfully")
            else:
                logger.error(f"Failed to save {display_name} data to MongoDB")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error in collect_and_save_single for {data_type}: {str(e)}", exc_info=True)
            return False
    
    def get_collection(self, data_type: str):
        """
        Get MongoDB collection for a specific type
        Args:
            data_type: Type of data ("gainers" or "losers")
        Returns: MongoDB collection object or None
        """
        if data_type == "gainers":
            return self.gainers_collection
        elif data_type == "losers":
            return self.losers_collection
        return None
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def main():
    """Main execution function"""
    collector = None
    try:
        collector = NSEGainersLosersCollector()
        # Collect both gainers and losers
        gainers_success = collector.collect_and_save_single("gainers")
        losers_success = collector.collect_and_save_single("losers")
        
        exit_code = 0 if (gainers_success and losers_success) else 1
        exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        exit(1)
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()

