# Quick Fix Instructions - VPS Cronjob Issues

## Problem
- Backend works but cron jobs don't run on VPS
- Time shows wrong: 9:12 AM IST saves as 03:30

## Quick Fix (5 Steps)

### Step 1: Fix Time on VPS (SSH into VPS)

```bash
# Copy and paste this entire block:
systemctl stop systemd-timesyncd
apt update -qq && apt install -y ntpdate 2>/dev/null || true
ntpdate -s pool.ntp.org
systemctl start systemd-timesyncd
hwclock --systohc
timedatectl set-ntp true
date
```

### Step 2: Upload Fixed Files (From Local Machine)

```bash
# In PowerShell or CMD, navigate to your project folder:
cd "C:\Users\HP\Desktop\X Fin Dataset"

# Upload files (replace YOUR_VPS_IP):
scp backend/timezone_utils.py root@YOUR_VPS_IP:/var/www/x-fin-dataset/backend/
scp backend/nse_fiidii_collector.py root@YOUR_VPS_IP:/var/www/x-fin-dataset/backend/
scp backend/admin_panel.py root@YOUR_VPS_IP:/var/www/x-fin-dataset/backend/
scp backend/check_schedulers_status.py root@YOUR_VPS_IP:/var/www/x-fin-dataset/backend/
scp deploy-timezone-fix.sh root@YOUR_VPS_IP:/var/www/x-fin-dataset/backend/
```

### Step 3: Deploy Fix on VPS (SSH into VPS)

```bash
cd /var/www/x-fin-dataset/backend
chmod +x deploy-timezone-fix.sh
./deploy-timezone-fix.sh
```

### Step 4: Check Scheduler Status

```bash
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3 check_schedulers_status.py
```

### Step 5: Verify

```bash
# Check PM2 logs for scheduler messages
pm2 logs x-fin-backend --lines 50 | grep -i scheduler

# Check if processes are running
ps aux | grep scheduler

# Check time
date
```

## What Was Fixed

1. ✅ **Timezone utility** - All timestamps now use IST timezone
2. ✅ **FII/DII collector** - Fixed to save IST time instead of UTC
3. ✅ **Better logging** - Schedulers now log when they start
4. ✅ **Diagnostic tool** - `check_schedulers_status.py` to diagnose issues

## Expected Results

After fix:
- ✅ Time shows correctly: `date` shows IST time
- ✅ PM2 shows backend running: `pm2 status`
- ✅ Schedulers appear in logs: `pm2 logs x-fin-backend | grep scheduler`
- ✅ Status files get updated: `ls -la *status.json`
- ✅ Timestamps in MongoDB are IST time (not UTC)

## If Still Not Working

1. **Check PM2 logs:**
   ```bash
   pm2 logs x-fin-backend --lines 100
   ```

2. **Manually test scheduler:**
   ```bash
   cd /var/www/x-fin-dataset/backend
   source venv/bin/activate
   python3 cronjob_scheduler.py
   ```
   (Should see scheduler messages - press Ctrl+C after a few seconds)

3. **Check for errors:**
   ```bash
   python3 check_schedulers_status.py
   ```

## Files Changed

- `backend/timezone_utils.py` - NEW: Timezone utility module
- `backend/nse_fiidii_collector.py` - FIXED: Uses IST time
- `backend/admin_panel.py` - IMPROVED: Better scheduler logging
- `backend/check_schedulers_status.py` - NEW: Diagnostic tool

---

**After these steps, your cron jobs should work and timestamps will be correct!**

