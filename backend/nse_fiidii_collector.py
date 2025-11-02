"""
NSE FII/DII Trade Data Collector
Collects data from NSE API and stores in MongoDB
Runs Monday to Friday at 5:00 PM
"""

import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime
import time
import logging
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nse_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
NSE_API_URL = "https://www.nseindia.com/api/fiidiiTradeReact"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME', 'fiidii_trades')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)


class NSEDataCollector:
    """Collects and stores NSE FII/DII trade data in MongoDB"""
    
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
            
            # Create unique index on date to prevent duplicates (one document per date)
            self.collection.create_index([("date", 1)], unique=True)
            
            logger.info(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def _fetch_data_with_retry(self) -> Optional[List[Dict]]:
        """
        Fetch data from NSE API with retry logic
        Returns: List of data or None if all retries fail
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/'
        }
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Attempting to fetch data from NSE API (Attempt {attempt}/{MAX_RETRIES})")
                
                response = requests.get(NSE_API_URL, headers=headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if not isinstance(data, list):
                    logger.error(f"Unexpected data format: {type(data)}")
                    if attempt < MAX_RETRIES:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    return None
                
                logger.info(f"Successfully fetched {len(data)} records from NSE API")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed")
                    
            except Exception as e:
                logger.error(f"Unexpected error (Attempt {attempt}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All retry attempts failed")
        
        return None
    
    def _save_to_mongo(self, data: List[Dict]) -> bool:
        """
        Save data to MongoDB, combining DII and FII into one document per date
        Returns: True if successful, False otherwise
        """
        if not data:
            logger.warning("No data to save")
            return False
        
        try:
            # Group records by date
            records_by_date = {}
            for record in data:
                date = record.get("date", "")
                category = record.get("category", "")
                
                if not date:
                    logger.warning(f"Skipping record with missing date: {record}")
                    continue
                
                if date not in records_by_date:
                    records_by_date[date] = {}
                
                # Map category to dii or fii
                if "DII" in category or "dii" in category.lower():
                    records_by_date[date]["dii"] = {
                        "buyValue": record.get("buyValue", ""),
                        "sellValue": record.get("sellValue", ""),
                        "netValue": record.get("netValue", "")
                    }
                elif "FII" in category or "FPI" in category or "fii" in category.lower() or "fpi" in category.lower():
                    records_by_date[date]["fii"] = {
                        "buyValue": record.get("buyValue", ""),
                        "sellValue": record.get("sellValue", ""),
                        "netValue": record.get("netValue", "")
                    }
            
            success_count = 0
            updated_count = 0
            
            # Save each date as a single document
            for date, categories in records_by_date.items():
                try:
                    update_doc = {
                        "$set": {
                            "updatedAt": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "insertedAt": datetime.utcnow()
                        }
                    }
                    
                    # Add DII data if available
                    if "dii" in categories:
                        update_doc["$set"]["dii"] = categories["dii"]
                    
                    # Add FII data if available
                    if "fii" in categories:
                        update_doc["$set"]["fii"] = categories["fii"]
                    
                    result = self.collection.update_one(
                        {"date": date},
                        update_doc,
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        success_count += 1
                        categories_list = ", ".join(categories.keys())
                        logger.info(f"Inserted new record for date: {date} with categories: {categories_list}")
                    elif result.modified_count > 0:
                        updated_count += 1
                        categories_list = ", ".join(categories.keys())
                        logger.info(f"Updated existing record for date: {date} with categories: {categories_list}")
                    else:
                        logger.debug(f"Record for date {date} already exists (no changes)")
                        
                except pymongo.errors.DuplicateKeyError:
                    logger.warning(f"Duplicate record skipped for date: {date}")
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving record for date {date}: {str(e)}")
            
            logger.info(f"Data save completed: {success_count} inserted, {updated_count} updated")
            return success_count > 0 or updated_count > 0
            
        except Exception as e:
            logger.error(f"Failed to save data to MongoDB: {str(e)}")
            return False
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect data and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Starting NSE data collection...")
            
            # Fetch data with retry
            data = self._fetch_data_with_retry()
            
            if data is None:
                logger.error("Failed to fetch data from NSE API after all retries")
                return False
            
            # Save to MongoDB
            success = self._save_to_mongo(data)
            
            if success:
                logger.info("NSE data collection completed successfully")
            else:
                logger.error("Failed to save data to MongoDB")
            
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
        collector = NSEDataCollector()
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

