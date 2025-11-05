"""
Test MongoDB Connection
Run this script to verify MongoDB connection is working correctly
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test MongoDB connection with various methods"""
    
    print("=" * 60)
    print("MongoDB Connection Test")
    print("=" * 60)
    
    # Method 1: Try MONGODB_URI
    mongodb_uri = os.getenv('MONGODB_URI')
    if mongodb_uri:
        print(f"\n1. Testing with MONGODB_URI:")
        print(f"   URI: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else mongodb_uri}")
        try:
            client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            client.server_info()
            print("   ✓ Connection successful!")
            
            # List databases
            dbs = client.list_database_names()
            print(f"   ✓ Available databases: {', '.join(dbs)}")
            
            # Test database access
            db_name = os.getenv('MONGO_DB_NAME', 'nse_data')
            if db_name in dbs or True:  # Database will be created if doesn't exist
                db = client[db_name]
                collections = db.list_collection_names()
                print(f"   ✓ Database '{db_name}' accessible")
                print(f"   ✓ Collections: {', '.join(collections) if collections else '(none)'}")
            
            client.close()
            return True
            
        except Exception as e:
            print(f"   ✗ Connection failed: {e}")
    
    # Method 2: Try individual environment variables
    print(f"\n2. Testing with individual environment variables:")
    mongo_host = os.getenv('MONGO_HOST', 'localhost')
    mongo_port = int(os.getenv('MONGO_PORT', 27017))
    mongo_db = os.getenv('MONGO_DB_NAME', 'nse_data')
    mongo_user = os.getenv('MONGO_USERNAME')
    mongo_pass = os.getenv('MONGO_PASSWORD')
    
    print(f"   Host: {mongo_host}")
    print(f"   Port: {mongo_port}")
    print(f"   Database: {mongo_db}")
    print(f"   Username: {mongo_user if mongo_user else '(not set)'}")
    
    try:
        if mongo_user and mongo_pass:
            # With authentication
            uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/{mongo_db}"
            auth_source = os.getenv('MONGO_AUTH_SOURCE', 'admin')
            uri += f"?authSource={auth_source}"
        else:
            # Without authentication
            uri = f"mongodb://{mongo_host}:{mongo_port}/{mongo_db}"
        
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.server_info()
        print("   ✓ Connection successful!")
        
        # List databases
        dbs = client.list_database_names()
        print(f"   ✓ Available databases: {', '.join(dbs)}")
        
        # Test database access
        db = client[mongo_db]
        collections = db.list_collection_names()
        print(f"   ✓ Database '{mongo_db}' accessible")
        print(f"   ✓ Collections: {', '.join(collections) if collections else '(none)'}")
        
        # Test write operation
        test_collection = db['connection_test']
        test_collection.insert_one({'test': 'connection', 'timestamp': 'test'})
        test_collection.delete_one({'test': 'connection'})
        print("   ✓ Write/Delete test successful!")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False
    
    # Method 3: Try default localhost connection
    print(f"\n3. Testing with default localhost connection:")
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
        client.server_info()
        print("   ✓ Connection successful!")
        
        dbs = client.list_database_names()
        print(f"   ✓ Available databases: {', '.join(dbs)}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = test_mongodb_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ MongoDB connection test PASSED")
        print("=" * 60)
        print("\nYour application should be able to connect to MongoDB.")
        print("You can now start your backend application.")
    else:
        print("✗ MongoDB connection test FAILED")
        print("=" * 60)
        print("\nPlease check:")
        print("1. Is MongoDB running? (sudo systemctl status mongod)")
        print("2. Is the connection string correct in .env file?")
        print("3. Are credentials correct (if using authentication)?")
        print("4. Is MongoDB accessible from localhost?")
        exit(1)

