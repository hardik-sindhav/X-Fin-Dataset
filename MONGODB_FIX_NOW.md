# MongoDB Authentication Fix - URGENT

## The Problem
You're getting: `Authentication failed., full error: {'ok': 0.0, 'errmsg': 'Authentication failed.', 'code': 18}`

**Why?** MongoDB requires the `authSource` parameter in the connection string to know which database contains your user credentials.

## Quick Fix (2 Steps)

### Step 1: Add to .env file (On VPS)

```bash
cd /var/www/x-fin-dataset/backend
nano .env
```

**Add this line:**
```env
MONGO_AUTH_SOURCE=admin
```

**Save and exit** (Ctrl+X, then Y, then Enter)

### Step 2: Fix All Files (On VPS)

**Upload the fix script:**
```bash
# From your local machine
scp backend/fix_all_mongodb_connections.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
scp backend/admin_panel.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
```

**On VPS, run the fix script:**
```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3 fix_all_mongodb_connections.py
```

**Restart backend:**
```bash
pm2 restart x-fin-backend
```

## What Changed

**Before (WRONG - causes error):**
```python
mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/"
```

**After (CORRECT - works):**
```python
MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
```

## Verify

```bash
# Check logs - should NOT see authentication errors
pm2 logs x-fin-backend --lines 20

# Test API
curl https://api.xfinai.cloud/api/mongodb/health
```

## Why This Is Needed

MongoDB authentication works like this:
1. User `xfinai` is created in the `admin` database
2. When connecting, MongoDB needs to know WHERE to look for this user
3. `authSource=admin` tells MongoDB: "Look for the user in the admin database"
4. Without `authSource`, MongoDB doesn't know where to authenticate and fails

## Alternative: Manual Fix

If the script doesn't work, manually edit each file:

1. Find this line in all collector files:
   ```python
   mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/"
   ```

2. Replace with:
   ```python
   MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE', 'admin')
   mongo_uri = f"mongodb://{encoded_username}:{encoded_password}@{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}"
   ```

Files to fix:
- `admin_panel.py` ✅ (already fixed)
- `nse_fiidii_collector.py`
- `nse_option_chain_collector.py`
- `nse_banknifty_option_chain_collector.py`
- All other `nse_*_collector.py` files

## After Fix

✅ MongoDB authentication will work  
✅ API endpoints will return data  
✅ Collectors will be able to save data  
✅ No more "Authentication failed" errors

---

**This fix is REQUIRED for MongoDB authentication to work!**

