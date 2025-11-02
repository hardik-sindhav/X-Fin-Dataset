"""
NSE Twitter Collector with Sentiment Analysis
Collects tweets related to BankNifty, Nifty50, and stock market
Runs Monday to Friday from 09:00 AM to 03:30 PM, every 15 minutes
"""

import snscrape.modules.twitter as sntwitter
from datetime import datetime
from textblob import TextBlob
import pytz
import pymongo
from pymongo import MongoClient
import logging
from typing import List, Dict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('twitter_collector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# MongoDB Configuration (can be overridden by environment variables)
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_TWITTER_COLLECTION_NAME', 'daily_tweets')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)

# Market hours
MARKET_START_HOUR = 9  # 9 AM
MARKET_END_HOUR = 15   # 3:30 PM (will check minutes too)
MARKET_END_MINUTE = 30

# Twitter search query keywords
TWITTER_QUERY = "(#banknifty OR #nifty50 OR #stockmarket OR #nseindia OR #bseindia OR #sensex OR #nifty OR #stockmarketindia) lang:en"
MAX_TWEETS_PER_RUN = 500


class NSETwitterCollector:
    """Collects tweets from Twitter and stores in MongoDB with sentiment analysis"""
    
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
            
            # Create unique index on (date, tweet_id) to prevent duplicate tweets
            self.collection.create_index([("date", 1), ("tweet_id", 1)], unique=True)
            
            # Create indexes for faster queries
            self.collection.create_index([("date", -1)])
            self.collection.create_index([("username", 1)])
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
    
    def fetch_tweets(self, max_tweets: int = MAX_TWEETS_PER_RUN) -> List[Dict]:
        """
        Fetch tweets related to BankNifty, Nifty50, and stock market
        Args:
            max_tweets: Maximum number of tweets to fetch
        Returns: List of tweet items
        """
        tweets = []
        try:
            # Get current date in IST
            ist = pytz.timezone("Asia/Kolkata")
            now_ist = datetime.now(ist)
            today = now_ist.date()
            today_str = today.strftime("%Y-%m-%d")
            
            # Build Twitter search query with date filter
            query = f"{TWITTER_QUERY} since:{today_str}"
            
            logger.info(f"Fetching tweets with query: {query}")
            logger.info(f"Maximum tweets to fetch: {max_tweets}")
            
            tweet_count = 0
            processed_count = 0
            
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
                if processed_count >= max_tweets:
                    break
                
                try:
                    # Convert tweet date to IST
                    if tweet.date.tzinfo is None:
                        tweet_date_utc = tweet.date.replace(tzinfo=pytz.UTC)
                    else:
                        tweet_date_utc = tweet.date.astimezone(pytz.UTC)
                    
                    tweet_date_ist = tweet_date_utc.astimezone(ist)
                    tweet_date = tweet_date_ist.date()
                    
                    # Only collect today's tweets during market hours (9 AM to 3:30 PM)
                    if tweet_date == today:
                        hour = tweet_date_ist.hour
                        minute = tweet_date_ist.minute
                        
                        # Check if within market hours (9:00 AM to 3:30 PM)
                        if hour < MARKET_START_HOUR:
                            continue
                        if hour > MARKET_END_HOUR:
                            continue
                        if hour == MARKET_END_HOUR and minute > MARKET_END_MINUTE:
                            continue
                        
                        # Analyze sentiment
                        sentiment = self.get_sentiment(tweet.content)
                        
                        # Get user info safely
                        username = tweet.user.username if tweet.user else "Unknown"
                        followers_count = tweet.user.followersCount if tweet.user and hasattr(tweet.user, 'followersCount') else 0
                        
                        # Get tweet metrics safely
                        retweet_count = tweet.retweetCount if hasattr(tweet, 'retweetCount') else 0
                        like_count = tweet.likeCount if hasattr(tweet, 'likeCount') else 0
                        
                        tweet_item = {
                            "date": today.isoformat(),
                            "tweet_id": str(tweet.id),
                            "username": username,
                            "followers_count": followers_count,
                            "content": tweet.content,
                            "retweet_count": retweet_count,
                            "like_count": like_count,
                            "sentiment": sentiment,
                            "tweet_date": tweet_date_ist,
                            "insertedAt": datetime.utcnow()
                        }
                        
                        tweets.append(tweet_item)
                        tweet_count += 1
                        
                        if tweet_count % 50 == 0:
                            logger.info(f"Collected {tweet_count} tweets so far...")
                    
                    processed_count += 1
                
                except Exception as e:
                    logger.warning(f"Error processing tweet: {str(e)}")
                    continue
            
            logger.info(f"Found {len(tweets)} tweets for today during market hours (processed {processed_count} total tweets)")
            return tweets
        
        except Exception as e:
            logger.error(f"Error fetching tweets: {str(e)}")
            return []
    
    def save_to_mongo(self, tweets: List[Dict]) -> int:
        """
        Save tweets to MongoDB
        Returns: Number of tweets saved successfully
        """
        if not tweets:
            logger.warning("No tweets to save")
            return 0
        
        saved_count = 0
        skipped_count = 0
        
        for tweet in tweets:
            try:
                # Remove insertedAt from tweet to avoid conflict with $setOnInsert
                tweet_copy = {k: v for k, v in tweet.items() if k != "insertedAt"}
                
                # Use upsert to avoid duplicates based on unique index
                result = self.collection.update_one(
                    {
                        "date": tweet["date"],
                        "tweet_id": tweet["tweet_id"]
                    },
                    {
                        "$set": {
                            **tweet_copy,
                            "updatedAt": datetime.utcnow()
                        },
                        "$setOnInsert": {
                            "insertedAt": tweet.get("insertedAt", datetime.utcnow())
                        }
                    },
                    upsert=True
                )
                
                if result.upserted_id:
                    saved_count += 1
                    logger.debug(f"Inserted tweet: {tweet['username']} - {tweet['content'][:50]}...")
                else:
                    skipped_count += 1
                    logger.debug(f"Skipped duplicate tweet: {tweet['username']} - {tweet['content'][:50]}...")
            
            except pymongo.errors.DuplicateKeyError:
                skipped_count += 1
                logger.debug(f"Duplicate tweet skipped: {tweet['username']} - {tweet['content'][:50]}...")
            
            except Exception as e:
                logger.error(f"Error saving tweet: {str(e)}")
        
        logger.info(f"Saved {saved_count} tweets, skipped {skipped_count} duplicates")
        return saved_count
    
    def collect_and_save(self) -> bool:
        """
        Main method to collect tweets and save to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Starting Twitter collection...")
            
            # Fetch tweets
            tweets = self.fetch_tweets(MAX_TWEETS_PER_RUN)
            
            if not tweets:
                logger.warning("No tweets found today during market hours")
                return False
            
            # Save to MongoDB
            saved_count = self.save_to_mongo(tweets)
            
            if saved_count > 0:
                logger.info(f"Twitter collection completed successfully. Saved {saved_count} tweets.")
                return True
            else:
                logger.warning("No new tweets saved (all were duplicates)")
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
        collector = NSETwitterCollector()
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

