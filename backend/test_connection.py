"""
Test script to verify MongoDB connection and API access
Run this before starting the cronjob to ensure everything is configured correctly
"""

from nse_fiidii_collector import NSEDataCollector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test MongoDB connection, API access, and save data to MongoDB"""
    try:
        logger.info("Testing MongoDB connection...")
        collector = NSEDataCollector()
        logger.info("[OK] MongoDB connection successful")
        
        logger.info("\nTesting API access and saving data to MongoDB...")
        # Use collect_and_save to fetch and save data
        success = collector.collect_and_save()
        
        if success:
            logger.info(f"[OK] Data successfully saved to MongoDB")
            
            # Display saved records count
            try:
                count = collector.collection.count_documents({})
                logger.info(f"[OK] Total records in MongoDB: {count}")
                
                # Show last 2 records
                recent_records = list(collector.collection.find().sort("insertedAt", -1).limit(2))
                logger.info("\nRecently saved records:")
                for record in recent_records:
                    record_display = {
                        "date": record.get("date"),
                        "dii": record.get("dii", {}),
                        "fii": record.get("fii", {})
                    }
                    logger.info(f"  - {record_display}")
            except Exception as e:
                logger.warning(f"Could not fetch saved records: {str(e)}")
        else:
            logger.error("[FAILED] Failed to save data to MongoDB")
        
        collector.close()
        logger.info("\n[OK] All tests completed!")
        return success
        
    except Exception as e:
        logger.error(f"[FAILED] Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()

