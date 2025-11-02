"""
Configuration file for NSE Data Collector
You can also use environment variables via .env file
"""

import os

# MongoDB Configuration
MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
MONGO_COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME', 'fiidii_trades')
MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)

# NSE API Configuration
NSE_API_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

