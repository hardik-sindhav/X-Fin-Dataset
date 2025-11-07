"""
NSE News Collector with Sentiment Analysis
Collects news from Google News RSS feeds and stores in MongoDB
Runs Monday to Friday from 09:00 AM to 03:30 PM, every 15 minutes
"""

import feedparser
from datetime import datetime, timedelta
from textblob import TextBlob
import pytz
import pymongo
from pymongo import MongoClient
import logging
from typing import List, Dict, Optional
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
        logging.FileHandler('news_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# List of banks and indices to collect news for
BANKS = [
    # Core Banks
    "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "SBI",
    "IndusInd Bank", "Federal Bank", "Bank of Baroda", "PNB", "IDFC First Bank",
    "AU Small Finance Bank", "IDBI Bank", "Nifty 50", "Bank Nifty",
    
  
    "RBI", "Monetary Policy", "Repo Rate", "Inflation India", "GDP India",
    "SEBI", "Union Budget India", "NBFC", "Fiscal Deficit", "Credit Growth India",
    
  
    "US Federal Reserve", "US Inflation", "Crude Oil Prices", "USD INR",
    "Global Recession", "China Economy", "Dollar Index", "Bond Yield",
    

    "FII Activity India", "DII Activity India", "Foreign Investment India",
    "Sensex", "NSE", "BSE",
    
   
    "Loan Default India", "NPA", "Credit Card Growth India", "Housing Loan",
    "Corporate Loan", "Bank Merger", "Digital Banking", "Fintech India", "UPI",
    
   
    "OPEC", "Middle East Tension", "Gold Price India",
    "Dollar Rupee",
    
  
    "Cyber Attack Bank", "AI in Banking", "Blockchain in Finance"
]

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_NEWS_COLLECTION_NAME', 'daily_news')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)

# Market hours
MARKET_START_HOUR = 9  # 9 AM
MARKET_END_HOUR = 15   # 3:30 PM (will check minutes too)
MARKET_END_MINUTE = 30


class NSENewsCollector:
    """Collects news from Google News RSS feeds and stores in MongoDB with sentiment analysis"""
    
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
            
            # Create unique index on (date, keyword, link) to prevent duplicates
            self.collection.create_index([("date", 1), ("keyword", 1), ("link", 1)], unique=True)
            
            # Create indexes for faster queries
            self.collection.create_index([("date", -1)])
            self.collection.create_index([("keyword", 1)])
            self.collection.create_index([("sentiment", 1)])
            
            logger.info(f"Successfully connected to MongoDB at {MONGO_HOST}:{MONGO_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def get_sentiment(self, text: str) -> str:
        """
        Analyze sentiment of text using TextBlob
        Returns: "Positive", "Negative", or "Neutral"
        """
        try:
            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.1:
                return "Positive"
            elif polarity < -0.1:
                return "Negative"
            else:
                return "Neutral"
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {str(e)}")
            return "Neutral"
    
    def fetch_news_for_keyword(self, keyword: str) -> List[Dict]:
        """
        Fetch news from Google News RSS for a specific keyword
        Args:
            keyword: Bank name or index name
        Returns: List of news items
        """
        news_items = []
        try:
            # Build Google News RSS URL
            query = keyword.replace(' ', '+')
            url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            logger.info(f"Fetching news for keyword: {keyword}")
            feed = feedparser.parse(url)
            
            # Get current date in IST
            ist = pytz.timezone("Asia/Kolkata")
            today = datetime.now(ist).date()
            
            for entry in feed.entries:
                try:
                    # Parse publication date
                    pub_date_parsed = entry.published_parsed
                    if not pub_date_parsed:
                        continue
                    
                    # Convert to datetime in IST
                    pub_date_utc = datetime(*pub_date_parsed[:6], tzinfo=pytz.UTC)
                    pub_date_ist = pub_date_utc.astimezone(ist)
                    
                    # Only collect today's news during market hours (9 AM to 3:30 PM)
                    if pub_date_ist.date() == today:
                        hour = pub_date_ist.hour
                        minute = pub_date_ist.minute
                        
                        # Check if within market hours (9:00 AM to 3:30 PM)
                        if hour < MARKET_START_HOUR:
                            continue
                        if hour > MARKET_END_HOUR:
                            continue
                        if hour == MARKET_END_HOUR and minute > MARKET_END_MINUTE:
                            continue
                        
                        # Extract news data
                        title = entry.title
                        link = entry.link
                        source = entry.get("source", {}).get("title", "Unknown") if hasattr(entry, "source") else "Unknown"
                        
                        # Analyze sentiment
                        sentiment = self.get_sentiment(title)
                        
                        news_item = {
                            "date": today.isoformat(),
                            "keyword": keyword,
                            "title": title,
                            "source": source,
                            "sentiment": sentiment,
                            "link": link,
                            "pub_date": pub_date_ist,
                            "insertedAt": now_for_mongo()
                        }
                        
                        news_items.append(news_item)
                        logger.debug(f"Found news: {keyword} - {title[:50]}... [{sentiment}]")
                
                except Exception as e:
                    logger.warning(f"Error processing news entry: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} news items for {keyword}")
            return news_items
        
        except Exception as e:
            logger.error(f"Error fetching news for {keyword}: {str(e)}")
            return []
    
    def save_to_mongo(self, news_items: List[Dict]) -> int:
        """
        Save news items to MongoDB
        Returns: Number of items saved successfully
        """
        if not news_items:
            logger.warning("No news items to save")
            return 0
        
        saved_count = 0
        skipped_count = 0
        
        for item in news_items:
            try:
                # Remove insertedAt from item to avoid conflict with $setOnInsert
                item_copy = {k: v for k, v in item.items() if k != "insertedAt"}
                
                # Use upsert to avoid duplicates based on unique index
                result = self.collection.update_one(
                    {
                        "date": item["date"],
                        "keyword": item["keyword"],
                        "link": item["link"]
                    },
                    {
                        "$set": {
                            **item_copy,
                            "updatedAt": now_for_mongo()
                        },
                        "$setOnInsert": {
                            "insertedAt": item.get("insertedAt", now_for_mongo())
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id:
                    saved_count += 1
                    logger.debug(f"Inserted news: {item['keyword']} - {item['title'][:50]}...")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped duplicate: {item['keyword']} - {item['title'][:50]}...")
            
            except pymongo.errors.DuplicateKeyError:
                skipped_count += 1
                logger.debug(f"Duplicate news skipped: {item['keyword']} - {item['title'][:50]}...")
            
            except Exception as e:
                logger.error(f"Error saving news item: {str(e)}")
        
        logger.info(f"Saved {saved_count} news items, skipped {skipped_count} duplicates")
        return saved_count
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect news for all keywords and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Starting news collection...")
            
            all_news_items = []
            
            # Collect news for each keyword
            for bank in BANKS:
                try:
                    news_items = self.fetch_news_for_keyword(bank)
                    all_news_items.extend(news_items)
                except Exception as e:
                    logger.error(f"Error collecting news for {bank}: {str(e)}")
                    continue
            
            if not all_news_items:
                logger.warning("No news items found today")
                return False
            
            # Save to MongoDB
            saved_count = self.save_to_mongo(all_news_items)
            
            if saved_count > 0:
                logger.info(f"News collection completed successfully. Saved {saved_count} items.")
                return True
            else:
                logger.warning("No new news items saved (all were duplicates)")
                return True  # Still consider successful if duplicates are skipped
        
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
        collector = NSENewsCollector()
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

