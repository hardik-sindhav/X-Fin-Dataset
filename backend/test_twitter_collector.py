"""
Test Script for Twitter Collector
Run this to test the Twitter collector functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from nse_twitter_collector import NSETwitterCollector
import logging

# Configure logging to see output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_twitter_collector():
    """Test the Twitter collector"""
    print("=" * 60)
    print("Testing Twitter Collector")
    print("=" * 60)
    
    collector = None
    try:
        # Initialize collector
        print("\n1. Initializing Twitter Collector...")
        collector = NSETwitterCollector()
        print("   ✅ MongoDB connection established")
        
        # Test fetching tweets
        print("\n2. Fetching tweets (this may take a while)...")
        print("   Note: Fetching up to 50 tweets for testing")
        tweets = collector.fetch_tweets(max_tweets=50)
        
        if tweets:
            print(f"   ✅ Successfully fetched {len(tweets)} tweets")
            print(f"\n   Sample tweets:")
            for i, tweet in enumerate(tweets[:3], 1):
                print(f"\n   Tweet {i}:")
                print(f"   - Username: @{tweet.get('username', 'Unknown')}")
                print(f"   - Content: {tweet.get('content', '')[:100]}...")
                print(f"   - Sentiment: {tweet.get('sentiment', 'Unknown')}")
                print(f"   - Likes: {tweet.get('like_count', 0)}")
                print(f"   - Retweets: {tweet.get('retweet_count', 0)}")
                print(f"   - Followers: {tweet.get('followers_count', 0)}")
        else:
            print("   ⚠️  No tweets found (might be outside market hours or no matching tweets)")
        
        # Test saving to MongoDB
        if tweets:
            print("\n3. Saving tweets to MongoDB...")
            saved_count = collector.save_to_mongo(tweets)
            print(f"   ✅ Successfully saved {saved_count} tweets to MongoDB")
            
            # Check database count
            total_count = collector.collection.count_documents({})
            print(f"   📊 Total tweets in database: {total_count}")
        else:
            print("\n3. Skipping save test (no tweets to save)")
        
        # Test full collect and save
        print("\n4. Testing full collect_and_save method...")
        print("   Note: This will fetch and save tweets")
        success = collector.collect_and_save()
        
        if success:
            print("   ✅ Collection completed successfully")
        else:
            print("   ⚠️  Collection completed but no new tweets were saved")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        if collector:
            collector.close()
            print("\n📝 MongoDB connection closed")
    
    return True

if __name__ == "__main__":
    print("\n")
    print("Twitter Collector Test Script")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Test MongoDB connection")
    print("2. Fetch sample tweets from Twitter")
    print("3. Save tweets to MongoDB")
    print("4. Run full collection process")
    print("\nNote: Make sure you have:")
    print("- MongoDB running")
    print("- Internet connection")
    print("- snscrape installed (pip install snscrape)")
    print("\n" + "=" * 60 + "\n")
    
    input("Press Enter to start testing...")
    
    test_twitter_collector()

