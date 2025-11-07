"""
NSE Top 20 Losers Data Collector
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
from urllib.parse import quote_plus
from timezone_utils import now_for_mongo

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('losers_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
LOSERS_API_URL = "https://www.nseindia.com/api/live-analysis-variations?index=loosers"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_LOSERS_COLLECTION_NAME', 'losers_data')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)


class NSELosersCollector:
    """Collects and stores NSE Top 20 Losers data in MongoDB"""
    
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
            self.collection = self.db[MONGO_COLLECTION_NAME]
            
            # Create unique index on timestamp to prevent duplicates
            # We'll use the first available timestamp from any section
            self.collection.create_index([("timestamp", 1)], unique=True)
            
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
    
    def _fetch_losers_data_with_retry(self) -> Optional[Dict]:
        """
        Fetch Top 20 Losers data from NSE API with retry logic
        Returns: Full API response as dict or None if all retries fail
        """
        headers = self._get_headers()
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching Top 20 Losers data (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(LOSERS_API_URL, headers=headers, timeout=30)
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
                    logger.error("Timestamp not found in losers response")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.info(f"Successfully fetched Top 20 Losers data. Timestamp: {timestamp}")
                
                # Add top-level timestamp for easier querying
                data['timestamp'] = timestamp
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for losers data")
                    
            except Exception as e:
                logger.error(f"Unexpected error (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed for losers data")
        
        return None
    
    def _save_to_mongo(self, data: Dict) -> bool:
        """
        Save entire losers response to MongoDB
        Uses timestamp field as unique identifier to prevent duplicates
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning("No data to save")
            return False
        
        try:
            # Extract timestamp for duplicate check
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
                logger.error("Cannot save: timestamp not found in data")
                return False
            
            # Use upsert with timestamp as unique identifier
            result = self.collection.update_one(
                {"timestamp": timestamp},
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
                logger.info(f"Inserted new losers record with timestamp: {timestamp}")
                return True
            elif result.modified_count > 0:
                logger.info(f"Updated existing losers record with timestamp: {timestamp}")
                return True
            else:
                logger.debug(f"Losers record with timestamp {timestamp} already exists (no changes)")
                return True  # Still considered successful if no duplicates
                
        except pymongo.errors.DuplicateKeyError:
            logger.warning(f"Duplicate losers record skipped for timestamp: {timestamp}")
            return True  # Duplicate prevention working correctly
            
        except Exception as e:
            logger.error(f"Failed to save losers data to MongoDB: {str(e)}")
            return False
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect losers data and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Starting NSE Top 20 Losers data collection...")
            
            # Fetch losers data
            losers_data = self._fetch_losers_data_with_retry()
            
            if losers_data is None:
                logger.error("Failed to fetch losers data after all retries")
                return False
            
            # Save entire response to MongoDB
            success = self._save_to_mongo(losers_data)
            
            if success:
                logger.info("NSE Top 20 Losers data collection completed successfully")
            else:
                logger.error("Failed to save losers data to MongoDB")
            
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
        collector = NSELosersCollector()
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

