"""
MongoDB Connection Helper
Provides a function to build MongoDB connection string with proper authentication
"""

import os
from urllib.parse import quote_plus

def build_mongo_uri():
    """
    Build MongoDB connection URI with proper authentication
    Returns the connection URI string
    """
    MONGO_HOST = os.getenv('MONGO_HOST', 'localhost')
    MONGO_PORT = int(os.getenv('MONGO_PORT', 27017))
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nse_data')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', None)
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', None)
    MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
    
    if MONGO_USERNAME and MONGO_PASSWORD:
        # URL-encode username and password to handle special characters
        encoded_username = quote_plus(MONGO_USERNAME)
        encoded_password = quote_plus(MONGO_PASSWORD)
        # Include authSource parameter - MongoDB requires this for authentication
        mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
    else:
        mongo_uri = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"
    
    return mongo_uri

