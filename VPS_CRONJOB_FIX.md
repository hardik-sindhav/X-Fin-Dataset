# VPS Cronjob Fix Guide - Timezone & Scheduler Issues

## Problem Summary
1. **Backend working** but **no cron jobs running** on VPS
2. **Time mismatch**: When you trigger at 9:12 AM IST, it saves as 03:30 (timezone issue)
3. **Schedulers not starting** on VPS (works locally)

## Root Causes

### 1. Timezone Issue
- Code uses `datetime.utcnow()` which saves UTC time
- When you trigger at 9:12 AM IST, it's actually 3:42 AM UTC (9:12 - 5:30 = 3:42)
- MongoDB displays UTC time, causing confusion

### 2. Schedulers Not Running
- Schedulers are started in background threads from `admin_panel.py`
- If backend crashes or doesn't start, schedulers won't run
- No error logging makes it hard to diagnose

## Step-by-Step Fix

### Step 1: Fix Time Sync on VPS

SSH into your VPS and run:

```bash
# Fix time sync
systemctl stop systemd-timesyncd
apt update -qq && apt install -y ntpdate 2>/dev/null || true
ntpdate -s pool.ntp.org || ntpdate -s time.nist.gov
systemctl start systemd-timesyncd
hwclock --systohc
timedatectl set-ntp true
systemctl restart systemd-timesyncd

# Verify time
date
timedatectl status
```

### Step 2: Upload Fixed Code

On your **local machine**, upload the fixed files:

```bash
# Upload timezone utility and fixed collector
scp backend/timezone_utils.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
scp backend/nse_fiidii_collector.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
scp backend/admin_panel.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
scp backend/check_schedulers_status.py root@your-vps-ip:/var/www/x-fin-dataset/backend/
```

### Step 3: Install/Update Dependencies

On your **VPS**:

```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate

# Ensure pytz is installed (should already be in requirements.txt)
pip install pytz==2024.1

# Verify installation
python3 -c "import pytz; print('pytz installed:', pytz.__version__)"
```

### Step 4: Restart Backend

```bash
cd /var/www/x-fin-dataset/backend

# Restart PM2 backend
pm2 restart x-fin-backend

# Check status
pm2 status

# View logs to see if schedulers start
pm2 logs x-fin-backend --lines 50
```

### Step 5: Run Diagnostic Script

```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3 check_schedulers_status.py
```

This will show you:
- PM2 process status
- Running Python processes
- Scheduler status files
- System time and timezone
- Configuration status

## What Was Fixed

### 1. Timezone Utility (`timezone_utils.py`)
- Created consistent timezone handling for IST
- All timestamps now use IST timezone
- MongoDB stores IST time (not UTC)

### 2. Fixed FII/DII Collector
- Changed `datetime.utcnow()` to `now_for_mongo()` (IST time)
- Timestamps now saved in IST timezone

### 3. Better Logging
- Added logging when schedulers start
- Better error messages in scheduler threads

### 4. Diagnostic Script
- `check_schedulers_status.py` helps diagnose issues

## Verify Fix

### Check Time in Database
After fix, when you trigger at 9:12 AM IST, it should save as 9:12 AM (IST time), not 03:30.

### Check Schedulers Are Running

```bash
# Method 1: Check PM2 logs
pm2 logs x-fin-backend | grep -i scheduler

# Method 2: Check Python processes
ps aux | grep scheduler

# Method 3: Run diagnostic
cd /var/www/x-fin-dataset/backend
python3 check_schedulers_status.py
```

### Check Scheduler Status Files

```bash
cd /var/www/x-fin-dataset/backend
ls -la *scheduler*status.json
cat scheduler_status.json
```

Status files should show recent `last_run` timestamps.

## Troubleshooting

### If Schedulers Still Don't Run

1. **Check PM2 is running:**
   ```bash
   pm2 status
   pm2 logs x-fin-backend --lines 100
   ```

2. **Check for import errors:**
   ```bash
   cd /var/www/x-fin-dataset/backend
   source venv/bin/activate
   python3 -c "from timezone_utils import now_for_mongo; print('OK')"
   ```

3. **Manually test a scheduler:**
   ```bash
   cd /var/www/x-fin-dataset/backend
   source venv/bin/activate
   python3 cronjob_scheduler.py
   ```
   (Press Ctrl+C after a few seconds to stop)

4. **Check system logs:**
   ```bash
   journalctl -xe | tail -50
   ```

### If Time Is Still Wrong

1. **Force time sync:**
   ```bash
   ntpdate -s pool.ntp.org
   hwclock --systohc
   ```

2. **Verify timezone:**
   ```bash
   timedatectl set-timezone Asia/Kolkata
   timedatectl status
   ```

3. **Check MongoDB timezone:**
   MongoDB itself doesn't have timezone settings, but timestamps should be stored in IST.

## Next Steps (Optional)

To fix ALL collectors (not just FII/DII), you'll need to update all files that use `datetime.utcnow()`. The pattern is:

**Before:**
```python
"updatedAt": datetime.utcnow()
```

**After:**
```python
from timezone_utils import now_for_mongo
"updatedAt": now_for_mongo()
```

Files to update:
- `nse_option_chain_collector.py`
- `nse_gainers_collector.py`
- `nse_losers_collector.py`
- `nse_news_collector.py`
- All bank option chain collectors
- And all other collectors

## Quick Commands Reference

```bash
# Fix time
systemctl stop systemd-timesyncd && ntpdate -s pool.ntp.org && systemctl start systemd-timesyncd && hwclock --systohc

# Restart backend
cd /var/www/x-fin-dataset/backend && pm2 restart x-fin-backend

# Check schedulers
cd /var/www/x-fin-dataset/backend && python3 check_schedulers_status.py

# View logs
pm2 logs x-fin-backend --lines 50

# Check time
date && timedatectl status
```

## Success Indicators

✅ **Time is correct**: `date` shows correct IST time  
✅ **PM2 running**: `pm2 status` shows x-fin-backend as online  
✅ **Schedulers running**: `ps aux | grep scheduler` shows processes  
✅ **Status files updated**: `scheduler_status.json` has recent `last_run`  
✅ **Timestamps correct**: MongoDB shows IST time, not UTC

---

**After applying these fixes, your cron jobs should start running and timestamps should be correct!**

