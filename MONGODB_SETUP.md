# MongoDB Setup Guide for VPS

Complete guide to configure MongoDB on your VPS and connect it to your application.

## Step 1: Verify MongoDB Installation

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# If not running, start it
sudo systemctl start mongod
sudo systemctl enable mongod  # Enable auto-start on boot

# Check MongoDB version
mongosh --version
# or
mongo --version  # (older versions)
```

## Step 2: Test MongoDB Connection

```bash
# Connect to MongoDB shell
mongosh
# or for older versions: mongo

# In MongoDB shell, test basic commands:
show dbs
use nse_data
db.test.insertOne({test: "connection"})
db.test.find()
db.test.drop()
exit
```

## Step 3: Configure MongoDB for Production (Recommended)

### Option A: Without Authentication (Development/Testing Only)

If you're just testing, you can use MongoDB without authentication. Your connection string will be:
```
mongodb://localhost:27017/nse_data
```

### Option B: With Authentication (Production - Recommended)

For production, set up MongoDB authentication:

```bash
# Connect to MongoDB
mongosh

# Switch to admin database
use admin

# Create admin user
db.createUser({
  user: "admin",
  pwd: "your-secure-password-here",  # Change this!
  roles: [ { role: "root", db: "admin" } ]
})

# Create application user (more secure)
use nse_data
db.createUser({
  user: "nse_app",
  pwd: "your-app-password-here",  # Change this!
  roles: [
    { role: "readWrite", db: "nse_data" },
    { role: "dbAdmin", db: "nse_data" }
  ]
})

exit
```

### Enable Authentication in MongoDB

```bash
# Edit MongoDB configuration
sudo nano /etc/mongod.conf
```

Add or uncomment the security section:
```yaml
security:
  authorization: enabled
```

```bash
# Restart MongoDB
sudo systemctl restart mongod

# Verify it's running
sudo systemctl status mongod
```

## Step 4: Configure Backend .env File

```bash
cd /var/www/x-fin-dataset/backend
nano .env
```

### For MongoDB without authentication:
```env
MONGODB_URI=mongodb://localhost:27017/nse_data
```

### For MongoDB with authentication:
```env
# Using admin user (full access)
MONGODB_URI=mongodb://admin:your-secure-password@localhost:27017/nse_data?authSource=admin

# OR using application user (recommended)
MONGODB_URI=mongodb://nse_app:your-app-password@localhost:27017/nse_data?authSource=nse_data
```

### Alternative: Using Individual Environment Variables

Your collectors also support individual MongoDB environment variables:

```env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=nse_data
MONGO_USERNAME=nse_app
MONGO_PASSWORD=your-app-password
MONGO_AUTH_SOURCE=nse_data
```

## Step 5: Test Connection from Python

```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate

# Test MongoDB connection
python3.11 -c "
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/nse_data')
print(f'Connecting to: {uri.replace(os.getenv(\"MONGO_PASSWORD\", \"\"), \"***\")}')

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection
    print('✓ MongoDB connection successful!')
    print(f'Available databases: {client.list_database_names()}')
    db = client['nse_data']
    collections = db.list_collection_names()
    print(f'Collections in nse_data: {collections if collections else \"(none)\"}')
except Exception as e:
    print(f'✗ MongoDB connection failed: {e}')
"
```

## Step 6: Create Required Collections

Your application will create collections automatically, but you can verify:

```bash
mongosh

use nse_data

# Check existing collections
show collections

# If you want to create indexes manually (optional):
db.fiidii_trades.createIndex({ "date": 1 })
db.option_chain_data.createIndex({ "timestamp": 1 })
db.banknifty_option_chain_data.createIndex({ "timestamp": 1 })

exit
```

## Step 7: Verify Application Can Write Data

```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate

# Test a collector manually
python3.11 -c "
from nse_fiidii_collector import NSEDataCollector
collector = NSEDataCollector()
print('Testing MongoDB connection...')
try:
    # Check if we can access the database
    db = collector.db
    collections = db.list_collection_names()
    print(f'✓ Connected to database: {db.name}')
    print(f'✓ Existing collections: {collections}')
    collector.close()
    print('✓ Connection test successful!')
except Exception as e:
    print(f'✗ Connection test failed: {e}')
"
```

## Step 8: MongoDB Security Best Practices

### 1. Bind MongoDB to Localhost Only (Recommended)

```bash
sudo nano /etc/mongod.conf
```

Make sure network binding is:
```yaml
net:
  bindIp: 127.0.0.1  # Only localhost
  port: 27017
```

### 2. Set Up Firewall

```bash
# MongoDB should only be accessible from localhost
# Verify no external access
sudo ufw status
# MongoDB port 27017 should NOT be open to external
```

### 3. Regular Backups

```bash
# Create backup directory
mkdir -p /backup/mongodb

# Manual backup
mongodump --out /backup/mongodb/backup-$(date +%Y%m%d-%H%M%S)

# Restore from backup
mongorestore /backup/mongodb/backup-YYYYMMDD-HHMMSS
```

### 4. Set Up Automated Backups (Optional)

```bash
# Create backup script
sudo nano /usr/local/bin/mongodb-backup.sh
```

Add:
```bash
#!/bin/bash
BACKUP_DIR="/backup/mongodb"
DATE=$(date +%Y%m%d-%H%M%S)
mongodump --out "$BACKUP_DIR/backup-$DATE"
# Keep only last 7 days
find "$BACKUP_DIR" -type d -name "backup-*" -mtime +7 -exec rm -rf {} +
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/mongodb-backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/mongodb-backup.sh
```

## Step 9: Monitor MongoDB

```bash
# Check MongoDB status
sudo systemctl status mongod

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Check MongoDB stats
mongosh --eval "db.stats()"

# Check database size
mongosh nse_data --eval "db.stats(1024*1024)"  # Size in MB
```

## Troubleshooting

### MongoDB not starting

```bash
# Check logs
sudo tail -50 /var/log/mongodb/mongod.log

# Check if port is in use
sudo netstat -tulpn | grep 27017

# Check MongoDB process
ps aux | grep mongod

# Restart MongoDB
sudo systemctl restart mongod
```

### Connection refused errors

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Check if binding is correct
sudo cat /etc/mongod.conf | grep bindIp

# Test connection
mongosh mongodb://localhost:27017
```

### Authentication errors

```bash
# Verify user exists
mongosh --authenticationDatabase admin -u admin -p
use nse_data
db.getUsers()

# Reset password (if needed)
mongosh --authenticationDatabase admin -u admin -p
use nse_data
db.changeUserPassword("nse_app", "new-password")
```

### Permission denied errors

```bash
# Check MongoDB data directory permissions
sudo ls -la /var/lib/mongodb

# Fix permissions if needed
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chmod -R 755 /var/lib/mongodb
```

## Quick Reference

### MongoDB Connection Strings

**Local without auth:**
```
mongodb://localhost:27017/nse_data
```

**Local with auth:**
```
mongodb://username:password@localhost:27017/nse_data?authSource=admin
```

**MongoDB Atlas (Cloud):**
```
mongodb+srv://username:password@cluster.mongodb.net/nse_data?retryWrites=true&w=majority
```

### Common Commands

```bash
# Start MongoDB
sudo systemctl start mongod

# Stop MongoDB
sudo systemctl stop mongod

# Restart MongoDB
sudo systemctl restart mongod

# Check status
sudo systemctl status mongod

# Connect to shell
mongosh
# or with auth: mongosh -u admin -p --authenticationDatabase admin

# View databases
mongosh --eval "show dbs"

# View collections
mongosh nse_data --eval "show collections"

# Backup database
mongodump --out /backup/mongodb/backup-$(date +%Y%m%d)

# Restore database
mongorestore /backup/mongodb/backup-YYYYMMDD
```

## Next Steps

1. ✅ Verify MongoDB is running
2. ✅ Configure .env file with MongoDB URI
3. ✅ Test connection from Python
4. ✅ Start your backend application
5. ✅ Verify data is being collected

After completing these steps, your application should be able to connect to MongoDB and start collecting data!

