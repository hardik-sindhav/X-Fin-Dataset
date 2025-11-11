"""
NSE All Gainers and Losers Data Collector
Collects data from NSE API for both gainers and losers and stores in MongoDB
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
from urllib.parse import quote_plus
from timezone_utils import now_for_mongo
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

# Define gainers and losers configuration
GAINERS_LOSERS = [
    {
        "type": "gainers",
        "api_url": GAINERS_API_URL,
        "collection_name": os.getenv('MONGO_GAINERS_COLLECTION_NAME', 'gainers_data'),
        "display_name": "Top 20 Gainers"
    },
    {
        "type": "losers",
        "api_url": LOSERS_API_URL,
        "collection_name": os.getenv('MONGO_LOSERS_COLLECTION_NAME', 'losers_data'),
        "display_name": "Top 20 Losers"
    }
]


class NSEAllGainersLosersCollector:
    """Collects and stores NSE Top 20 Gainers and Losers data in MongoDB"""
    
    def __init__(self):
        """Initialize MongoDB connections for both gainers and losers"""
        self.client = None
        self.db = None
        self.collections = {}  # Dictionary to store collections: {"gainers": collection, "losers": collection}
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
            
            # Initialize collections for both gainers and losers
            for config in GAINERS_LOSERS:
                collection = self.db[config["collection_name"]]
                # Create unique index on collectedAt to ensure each collection run creates a new record
                # Also create non-unique index on timestamp for querying
                try:
                    collection.create_index([("collectedAt", 1)], unique=True)
                    collection.create_index([("timestamp", 1)])  # Non-unique for querying
                except Exception as e:
                    # Index might already exist, that's okay
                    logger.debug(f"Index creation note for {config['collection_name']}: {str(e)}")
                self.collections[config["type"]] = collection
                logger.debug(f"Initialized collection for {config['display_name']}: {config['collection_name']}")
            
            logger.debug(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
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
        display_name = next((c["display_name"] for c in GAINERS_LOSERS if c["type"] == data_type), data_type)
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug(f"Fetching {display_name} data (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                # Validate response structure
                if not isinstance(data, dict):
                    logger.error(f"Unexpected data format for {data_type}: {type(data)}")
                    if attempt < MAX_RETRIES:
                        logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                # Check if we have at least one timestamp in the response
                # Try to get timestamp from first available section
                timestamp = None
                for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                    if key in data and isinstance(data[key], dict):
                        section_timestamp = data[key].get('timestamp')
                        if section_timestamp:
                            timestamp = section_timestamp
                            break
                
                if not timestamp:
                    logger.error(f"Timestamp not found in {data_type} response")
                    if attempt < MAX_RETRIES:
                        logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.debug(f"Successfully fetched {display_name} data. Timestamp: {timestamp}")
                
                # Add top-level timestamp for easier querying
                data['timestamp'] = timestamp
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for {data_type} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {data_type} data")
                    
            except Exception as e:
                logger.error(f"Unexpected error for {data_type} (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"All retry attempts failed for {data_type} data")
        
        return None
    
    def _save_to_mongo(self, data_type: str, data: Dict) -> bool:
        """
        Save entire response to MongoDB for a specific type
        Uses collectedAt field as unique identifier to ensure each collection run creates a new record
        Args:
            data_type: Type of data ("gainers" or "losers")
            data: Data dictionary to save
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning(f"No data to save for {data_type}")
            return False
        
        try:
            collection = self.collections.get(data_type)
            if collection is None:
                logger.error(f"Collection not found for {data_type}")
                return False
            
            # Extract timestamp from NSE API response
            # Use top-level timestamp if available, otherwise extract from sections
            timestamp = data.get('timestamp')
            if not timestamp:
                # Try to get timestamp from first available section
                for key in ['NIFTY', 'BANKNIFTY', 'NIFTYNEXT50', 'allSec', 'FOSec']:
                    if key in data and isinstance(data[key], dict):
                        section_timestamp = data[key].get('timestamp')
                        if section_timestamp:
                            timestamp = section_timestamp
                            data['timestamp'] = timestamp  # Add to top level for consistency
                            break
            
            if not timestamp:
                logger.error(f"Cannot save {data_type}: timestamp not found in data")
                return False
            
            # Use collectedAt (collection time) as unique identifier
            # This ensures each collection run creates a new record, even if NSE timestamp is the same
            collected_at = now_for_mongo()
            collected_at_str = collected_at.isoformat()
            
            # Use upsert with collectedAt as unique identifier
            result = collection.update_one(
                {"collectedAt": collected_at},
                {
                    "$set": {
                        **data,
                        "updatedAt": collected_at
                    },
                    "$setOnInsert": {
                        "insertedAt": collected_at,
                        "collectedAt": collected_at
                    }
                },
                upsert=True
            )
            
            if result.upserted_id:
                logger.debug(f"Inserted new {data_type} record with collectedAt: {collected_at_str}, NSE timestamp: {timestamp}")
                return True
            elif result.modified_count > 0:
                logger.debug(f"Updated existing {data_type} record with collectedAt: {collected_at_str}, NSE timestamp: {timestamp}")
                return True
            else:
                logger.debug(f"{data_type.capitalize()} record with collectedAt {collected_at_str} already exists (no changes)")
                return True  # Still considered successful if no duplicates
                
        except pymongo.errors.DuplicateKeyError:
            logger.debug(f"Duplicate {data_type} record skipped for collectedAt: {collected_at_str if 'collected_at_str' in locals() else 'unknown'}")
            return True  # Duplicate prevention working correctly
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to save {data_type} data to MongoDB: {error_msg}")
            return False
    
    def collect_and_save_all(self) -> Dict[str, bool]:
        """
        Collect and save data for both gainers and losers
        Returns: Dictionary with results for each type {"gainers": True/False, "losers": True/False}
        """
        results = {}
        
        for config in GAINERS_LOSERS:
            data_type = config["type"]
            display_name = config["display_name"]
            
            try:
                logger.debug(f"Starting {display_name} data collection...")
                
                # Fetch data
                data = self._fetch_data_with_retry(config["api_url"], data_type)
                
                if data is None:
                    logger.warning(f"Failed to fetch {display_name} data after all retries")
                    results[data_type] = False
                    continue
                
                # Save to MongoDB
                success = self._save_to_mongo(data_type, data)
                
                if success:
                    logger.debug(f"{display_name} data collection completed successfully")
                    results[data_type] = True
                else:
                    logger.warning(f"Failed to save {display_name} data to MongoDB")
                    results[data_type] = False
                    
            except Exception as e:
                logger.error(f"Unexpected error collecting {display_name}: {str(e)}")
                results[data_type] = False
        
        return results
    
    def collect_and_save_single(self, data_type: str) -> bool:
        """
        Collect and save data for a single type (gainers or losers)
        Args:
            data_type: Type of data ("gainers" or "losers")
        Returns: True if successful (including duplicates), False only on critical errors
        """
        config = next((c for c in GAINERS_LOSERS if c["type"] == data_type), None)
        if not config:
            logger.error(f"Invalid data type: {data_type}")
            return False
        
        display_name = config["display_name"]
        
        try:
            logger.debug(f"Starting {display_name} data collection...")
            
            # Fetch data
            data = self._fetch_data_with_retry(config["api_url"], data_type)
            
            if data is None:
                logger.warning(f"Failed to fetch {display_name} data after all retries - will retry on next run")
                return False
            
            # Save to MongoDB (returns True even for duplicates)
            success = self._save_to_mongo(data_type, data)
            
            if success:
                logger.debug(f"{display_name} data collection completed successfully")
            else:
                logger.warning(f"Failed to save {display_name} data to MongoDB - will retry on next run")
            
            return success
            
        except Exception as e:
            logger.error(f"Unexpected error collecting {display_name}: {str(e)}", exc_info=True)
            # Return False but don't crash - scheduler will continue
            return False
    
    def get_collection(self, data_type: str):
        """
        Get MongoDB collection for a specific type
        Args:
            data_type: Type of data ("gainers" or "losers")
        Returns: MongoDB collection object or None
        """
        return self.collections.get(data_type)
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.debug("MongoDB connection closed")


def main():
    """Main execution function"""
    collector = None
    try:
        collector = NSEAllGainersLosersCollector()
        results = collector.collect_and_save_all()
        
        # Check if all succeeded
        all_success = all(results.values())
        exit_code = 0 if all_success else 1
        exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        exit(1)
    finally:
        if collector:
            collector.close()


if __name__ == "__main__":
    main()

