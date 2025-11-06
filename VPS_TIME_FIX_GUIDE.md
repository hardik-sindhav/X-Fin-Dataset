# VPS Time Sync and Cron Job Fix Guide

## Problem
Your Hostinger VPS shows incorrect time (9:09 AM when it should be 9:12 AM) and cron jobs are not running.

## Quick Fix (Run on VPS)

### Option 1: Run the Fix Script (Recommended)

1. **Upload the fix script to your VPS:**
   ```bash
   # From your local machine, upload the script
   scp fix-vps-time-and-cron.sh root@your-vps-ip:/root/
   ```

2. **SSH into your VPS and run:**
   ```bash
   ssh root@your-vps-ip
   chmod +x /root/fix-vps-time-and-cron.sh
   /root/fix-vps-time-and-cron.sh
   ```

### Option 2: Manual Fix Commands

Run these commands on your VPS one by one:

```bash
# 1. Stop NTP service temporarily
systemctl stop systemd-timesyncd

# 2. Force sync time (install ntpdate if needed: apt install ntpdate -y)
ntpdate -s pool.ntp.org || ntpdate -s time.nist.gov

# 3. Restart and enable NTP service
systemctl start systemd-timesyncd
systemctl enable systemd-timesyncd
systemctl restart systemd-timesyncd

# 4. Sync hardware clock
hwclock --systohc
timedatectl set-ntp true

# 5. Verify time
timedatectl status
date

# 6. Check cron service
systemctl status cron
systemctl start cron
systemctl enable cron

# 7. Check PM2 services (your Python schedulers)
pm2 status
pm2 logs --lines 50

# 8. Restart PM2 services if needed
cd /var/www/x-fin-dataset/backend
pm2 restart all
pm2 save
```

## Diagnosing the Issue

### Check Current Time Status
```bash
timedatectl status
```

### Check NTP Sync Status
```bash
# If using systemd-timesyncd
systemctl status systemd-timesyncd

# If using chronyd
chronyc tracking

# If using ntpd
ntpq -p
```

### Check Cron Service
```bash
# Check if cron is running
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -20

# Check cron configuration
crontab -l
```

### Check PM2 Services
```bash
# List all PM2 processes
pm2 list

# Check PM2 logs
pm2 logs --lines 100

# Restart all PM2 processes
pm2 restart all
```

## Common Issues and Solutions

### Issue 1: Time Drift (2-3 minutes off)
**Solution:**
```bash
# Force immediate NTP sync
systemctl stop systemd-timesyncd
ntpdate -s pool.ntp.org
systemctl start systemd-timesyncd
hwclock --systohc
```

### Issue 2: Cron Jobs Not Running
**Possible causes:**
1. Cron service not running
2. Wrong timezone affecting scheduled times
3. PM2 processes crashed
4. Python schedulers not started

**Solutions:**
```bash
# Start cron service
systemctl start cron
systemctl enable cron

# Check PM2 processes
pm2 status
pm2 restart all

# Check if Python schedulers are running
ps aux | grep scheduler
```

### Issue 3: Timezone Issues
**Solution:**
```bash
# Set correct timezone
timedatectl set-timezone Asia/Kolkata

# Verify
timedatectl status
```

### Issue 4: NTP Not Syncing
**Solution:**
```bash
# Install ntpdate if not available
apt update && apt install -y ntpdate

# Manually sync
ntpdate -s pool.ntp.org

# Restart NTP service
systemctl restart systemd-timesyncd
```

## Verify Everything is Working

### 1. Check Time
```bash
date
timedatectl status
```

### 2. Check Cron Service
```bash
systemctl status cron
```

### 3. Check PM2 Services
```bash
pm2 status
pm2 logs --lines 20
```

### 4. Check Python Schedulers
```bash
# Check if scheduler processes are running
ps aux | grep -E "(cronjob_scheduler|option_chain_scheduler)"

# Check PM2 logs for scheduler activity
pm2 logs x-fin-backend | grep -i scheduler
```

## Setting Up Automatic Time Sync

Ensure NTP sync is enabled and working automatically:

```bash
# Enable NTP sync
timedatectl set-ntp true

# Verify it's enabled
timedatectl status | grep "System clock synchronized"

# Should show: System clock synchronized: yes
```

## Monitoring

### Check Time Sync Status Daily
```bash
timedatectl status
```

### Monitor PM2 Services
```bash
# Watch PM2 processes
pm2 monit

# Check logs regularly
pm2 logs --lines 50
```

## If Problems Persist

1. **Check system logs:**
   ```bash
   journalctl -xe | tail -50
   ```

2. **Check NTP logs:**
   ```bash
   journalctl -u systemd-timesyncd | tail -50
   ```

3. **Restart all services:**
   ```bash
   systemctl restart systemd-timesyncd
   systemctl restart cron
   pm2 restart all
   ```

4. **Contact Hostinger support** if hardware clock is faulty

## Prevention

To prevent future time sync issues:

1. **Enable automatic NTP sync:**
   ```bash
   timedatectl set-ntp true
   systemctl enable systemd-timesyncd
   ```

2. **Monitor PM2 services:**
   ```bash
   pm2 startup  # Make PM2 start on boot
   pm2 save     # Save current process list
   ```

3. **Set up monitoring:**
   - Check `timedatectl status` regularly
   - Monitor PM2 logs for scheduler errors
   - Set up alerts if services go down

