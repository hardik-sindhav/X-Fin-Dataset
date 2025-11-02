"""
Script to view saved data in MongoDB
Run this to check what data has been saved
"""

from nse_fiidii_collector import NSEDataCollector
import logging
from pprint import pprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def view_saved_data():
    """Display all saved data from MongoDB"""
    collector = None
    try:
        logger.info("Connecting to MongoDB...")
        collector = NSEDataCollector()
        
        # Get total count
        total_count = collector.collection.count_documents({})
        logger.info(f"\nTotal records in MongoDB: {total_count}\n")
        
        if total_count == 0:
            logger.info("No records found in MongoDB.")
            return
        
        # Get all records sorted by date (newest first)
        records = list(collector.collection.find().sort("date", -1))
        
        logger.info("=" * 80)
        logger.info("SAVED DATA IN MONGODB:")
        logger.info("=" * 80)
        
        for record in records:
            logger.info("\nRecord:")
            record_data = {
                "date": record.get("date"),
                "dii": record.get("dii", {}),
                "fii": record.get("fii", {}),
                "insertedAt": record.get("insertedAt"),
                "updatedAt": record.get("updatedAt")
            }
            pprint(record_data)
            logger.info("-" * 80)
        
        # Display formatted by date
        logger.info("\n\nFormatted View:")
        logger.info("=" * 80)
        for record in records:
            date = record.get("date")
            logger.info(f"\nDate: {date}")
            
            dii = record.get("dii", {})
            if dii:
                logger.info(f"  DII:  Buy={dii.get('buyValue', 'N/A')}, Sell={dii.get('sellValue', 'N/A')}, Net={dii.get('netValue', 'N/A')}")
            else:
                logger.info(f"  DII:  No data")
            
            fii = record.get("fii", {})
            if fii:
                logger.info(f"  FII:  Buy={fii.get('buyValue', 'N/A')}, Sell={fii.get('sellValue', 'N/A')}, Net={fii.get('netValue', 'N/A')}")
            else:
                logger.info(f"  FII:  No data")
        
    except Exception as e:
        logger.error(f"Error viewing data: {str(e)}")
    finally:
        if collector:
            collector.close()

if __name__ == "__main__":
    view_saved_data()

