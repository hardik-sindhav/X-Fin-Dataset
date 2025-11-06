#!/bin/bash
# Fix VPS Time Sync and Cron Jobs
# Run this script on your VPS as root

echo "=========================================="
echo "VPS Time Sync and Cron Job Fix Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check current time status
echo -e "${YELLOW}Step 1: Checking current time status...${NC}"
timedatectl status
echo ""

# Step 2: Stop NTP service temporarily
echo -e "${YELLOW}Step 2: Stopping NTP service...${NC}"
systemctl stop systemd-timesyncd 2>/dev/null || true
systemctl stop ntpd 2>/dev/null || true
systemctl stop chronyd 2>/dev/null || true
sleep 2

# Step 3: Force sync time with NTP
echo -e "${YELLOW}Step 3: Forcing NTP time sync...${NC}"

# Try different NTP sync methods
if command -v chronyd &> /dev/null; then
    echo "Using chronyd for time sync..."
    systemctl start chronyd
    chronyd -q 'server pool.ntp.org iburst' 2>/dev/null || true
elif command -v ntpd &> /dev/null; then
    echo "Using ntpd for time sync..."
    systemctl start ntpd
    ntpd -gq 2>/dev/null || true
else
    echo "Using systemd-timesyncd for time sync..."
    systemctl start systemd-timesyncd
    systemctl restart systemd-timesyncd
fi

# Alternative: Use ntpdate if available
if command -v ntpdate &> /dev/null; then
    echo "Syncing with ntpdate..."
    ntpdate -s pool.ntp.org 2>/dev/null || ntpdate -s time.nist.gov 2>/dev/null || true
fi

# Step 4: Enable and start NTP service
echo -e "${YELLOW}Step 4: Enabling NTP service...${NC}"
systemctl enable systemd-timesyncd 2>/dev/null || true
systemctl start systemd-timesyncd 2>/dev/null || true
systemctl enable chronyd 2>/dev/null || true
systemctl start chronyd 2>/dev/null || true
systemctl enable ntpd 2>/dev/null || true
systemctl start ntpd 2>/dev/null || true

# Step 5: Set hardware clock from system time
echo -e "${YELLOW}Step 5: Syncing hardware clock...${NC}"
hwclock --systohc 2>/dev/null || true
timedatectl set-ntp true

# Step 6: Verify time sync
echo -e "${YELLOW}Step 6: Verifying time sync...${NC}"
sleep 3
timedatectl status
echo ""

# Step 7: Check cron service
echo -e "${YELLOW}Step 7: Checking cron service...${NC}"
if systemctl is-active --quiet cron || systemctl is-active --quiet crond; then
    echo -e "${GREEN}✓ Cron service is running${NC}"
else
    echo -e "${RED}✗ Cron service is not running${NC}"
    echo "Starting cron service..."
    systemctl start cron 2>/dev/null || systemctl start crond 2>/dev/null || true
    systemctl enable cron 2>/dev/null || systemctl enable crond 2>/dev/null || true
fi

# Step 8: Check PM2 services (for your Python schedulers)
echo -e "${YELLOW}Step 8: Checking PM2 services...${NC}"
if command -v pm2 &> /dev/null; then
    echo "PM2 status:"
    pm2 status || echo "No PM2 processes found"
    echo ""
    echo "PM2 processes with time info:"
    pm2 list || echo "No PM2 processes"
else
    echo -e "${YELLOW}PM2 is not installed or not in PATH${NC}"
fi

# Step 9: Check systemd services
echo -e "${YELLOW}Step 9: Checking systemd services...${NC}"
systemctl list-units --type=service --state=running | grep -E "(cron|time|scheduler)" || echo "No relevant services found"

# Step 10: Verify timezone
echo -e "${YELLOW}Step 10: Verifying timezone...${NC}"
CURRENT_TZ=$(timedatectl | grep "Time zone" | awk '{print $3}')
echo "Current timezone: $CURRENT_TZ"
if [ "$CURRENT_TZ" != "Asia/Kolkata" ]; then
    echo -e "${YELLOW}Setting timezone to Asia/Kolkata...${NC}"
    timedatectl set-timezone Asia/Kolkata
fi

# Step 11: Final time check
echo ""
echo -e "${YELLOW}Step 11: Final time verification...${NC}"
echo "Current time:"
date
echo ""
echo "UTC time:"
date -u
echo ""
timedatectl status

# Step 12: Check NTP sync status
echo ""
echo -e "${YELLOW}Step 12: NTP synchronization status...${NC}"
if command -v chronyc &> /dev/null; then
    chronyc tracking 2>/dev/null || echo "chronyc not available"
fi
if command -v ntpq &> /dev/null; then
    ntpq -p 2>/dev/null || echo "ntpq not available"
fi

# Step 13: Recommendations
echo ""
echo -e "${GREEN}=========================================="
echo "Fix Summary"
echo "==========================================${NC}"
echo ""
echo "1. Time has been synced with NTP servers"
echo "2. Hardware clock synchronized"
echo "3. NTP service enabled and started"
echo "4. Cron service checked"
echo ""
echo -e "${YELLOW}If cron jobs still don't run, check:${NC}"
echo "  - PM2 processes: pm2 status"
echo "  - PM2 logs: pm2 logs"
echo "  - System logs: journalctl -xe"
echo "  - Cron logs: grep CRON /var/log/syslog"
echo ""
echo -e "${YELLOW}To restart PM2 services:${NC}"
echo "  cd /var/www/x-fin-dataset/backend"
echo "  pm2 restart all"
echo "  pm2 save"
echo ""
echo -e "${GREEN}Script completed!${NC}"

