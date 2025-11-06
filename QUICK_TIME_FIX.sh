#!/bin/bash
# Quick Time Sync Fix - Copy and paste this entire block into your VPS terminal

echo "Fixing time sync..."
systemctl stop systemd-timesyncd 2>/dev/null
ntpdate -s pool.ntp.org 2>/dev/null || ntpdate -s time.nist.gov 2>/dev/null || (echo "Installing ntpdate..." && apt update -qq && apt install -y ntpdate && ntpdate -s pool.ntp.org)
systemctl start systemd-timesyncd 2>/dev/null
hwclock --systohc 2>/dev/null
timedatectl set-ntp true
systemctl restart systemd-timesyncd 2>/dev/null
systemctl restart cron 2>/dev/null || systemctl restart crond 2>/dev/null
sleep 2
echo "Time sync complete!"
echo ""
echo "Current time:"
date
echo ""
timedatectl status
echo ""
echo "Checking PM2 services..."
pm2 status 2>/dev/null || echo "PM2 not found or no processes"
echo ""
echo "Done! If cron jobs still don't work, restart PM2:"
echo "  cd /var/www/x-fin-dataset/backend && pm2 restart all"

