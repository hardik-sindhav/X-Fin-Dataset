"""
LiveMint News Collector
Collects news from LiveMint RSS feed (https://www.livemint.com/rss/markets) and stores in MongoDB
"""

import feedparser
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from textblob import TextBlob
import pytz
import pymongo
from pymongo import MongoClient
import logging
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('livemint_news_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# RSS Feed URL
LIVEMINT_RSS_URL = "https://www.livemint.com/rss/markets"

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_LIVEMINT_NEWS_COLLECTION_NAME', 'livemint_news')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)

# Market hours for LiveMint (07:00 AM to 03:30 PM)
MARKET_START_HOUR = 7   # 7 AM
MARKET_END_HOUR = 15    # 3:30 PM
MARKET_END_MINUTE = 30


class NSELiveMintNewsCollector:
    """Collects news from LiveMint RSS feed and stores in MongoDB with sentiment analysis"""
    
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
            
            # Create unique index on (date, link) to prevent duplicates
            self.collection.create_index([("date", 1), ("link", 1)], unique=True)
            
            # Create indexes for faster queries
            self.collection.create_index([("date", -1)])
            self.collection.create_index([("pub_date", -1)])
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
    
    def fetch_livemint_news(self) -> List[Dict]:
        """
        Fetch news from LiveMint RSS feed
        Returns: List of news items
        """
        news_items = []
        try:
            logger.info(f"Fetching news from LiveMint RSS: {LIVEMINT_RSS_URL}")
            feed = feedparser.parse(LIVEMINT_RSS_URL)
            
            # Get current date in IST
            ist = pytz.timezone("Asia/Kolkata")
            today = datetime.now(ist).date()
            
            if not feed.entries:
                logger.warning("No entries found in LiveMint RSS feed")
                return []
            
            for entry in feed.entries:
                try:
                    # Parse publication date
                    pub_date_parsed = entry.get('published_parsed')
                    if not pub_date_parsed:
                        # Try to parse from pubDate string
                        pub_date_str = entry.get('published', '')
                        if pub_date_str:
                            try:
                                pub_date_utc = parsedate_to_datetime(pub_date_str)
                            except:
                                logger.warning(f"Could not parse date: {pub_date_str}")
                                continue
                        else:
                            continue
                    else:
                        # Convert to datetime in UTC
                        pub_date_utc = datetime(*pub_date_parsed[:6], tzinfo=pytz.UTC)
                    
                    # Convert to IST
                    pub_date_ist = pub_date_utc.astimezone(ist)
                    
                    # Only collect today's news during market hours (7 AM to 3:30 PM)
                    if pub_date_ist.date() == today:
                        hour = pub_date_ist.hour
                        minute = pub_date_ist.minute
                        
                        # Check if within market hours (7:00 AM to 3:30 PM)
                        if hour < MARKET_START_HOUR:
                            continue
                        if hour > MARKET_END_HOUR:
                            continue
                        if hour == MARKET_END_HOUR and minute > MARKET_END_MINUTE:
                            continue
                        
                        # Extract news data
                        title = entry.get('title', '').strip()
                        link = entry.get('link', '').strip()
                        description = entry.get('description', '').strip()
                        
                        # Get source (LiveMint)
                        source = "LiveMint"
                        
                        # Get image URL if available
                        image_url = None
                        if hasattr(entry, 'media_content') and entry.media_content:
                            image_url = entry.media_content[0].get('url', '')
                        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                            image_url = entry.media_thumbnail[0].get('url', '')
                        
                        # Use title and description for sentiment analysis
                        sentiment_text = f"{title} {description}"
                        sentiment = self.get_sentiment(sentiment_text)
                        
                        news_item = {
                            "date": today.isoformat(),
                            "source": source,
                            "title": title,
                            "description": description,
                            "source_type": "livemint",
                            "sentiment": sentiment,
                            "link": link,
                            "image_url": image_url,
                            "pub_date": pub_date_ist,
                            "insertedAt": datetime.utcnow()
                        }
                        
                        news_items.append(news_item)
                        logger.debug(f"Found news: {title[:50]}... [{sentiment}]")
                
                except Exception as e:
                    logger.warning(f"Error processing news entry: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} news items from LiveMint")
            return news_items
        
        except Exception as e:
            logger.error(f"Error fetching LiveMint news: {str(e)}")
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
                        "link": item["link"]
                    },
                    {
                        "$set": {
                            **item_copy,
                            "updatedAt": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "insertedAt": item.get("insertedAt", datetime.utcnow())
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id:
                    saved_count += 1
                    logger.debug(f"Inserted news: {item['title'][:50]}...")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped duplicate: {item['title'][:50]}...")
            
            except pymongo.errors.DuplicateKeyError:
                skipped_count += 1
                logger.debug(f"Duplicate news skipped: {item['title'][:50]}...")
            
            except Exception as e:
                logger.error(f"Error saving news item: {str(e)}")
        
        logger.info(f"Saved {saved_count} news items, skipped {skipped_count} duplicates")
        return saved_count
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect news from LiveMint and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Starting LiveMint news collection...")
            
            # Fetch news from LiveMint RSS
            news_items = self.fetch_livemint_news()
            
            if not news_items:
                logger.warning("No news items found from LiveMint")
                return False
            
            # Save to MongoDB
            saved_count = self.save_to_mongo(news_items)
            
            if saved_count > 0:
                logger.info(f"LiveMint news collection completed successfully. Saved {saved_count} items.")
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
        collector = NSELiveMintNewsCollector()
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

