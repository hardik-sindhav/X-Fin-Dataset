# 🚀 Quick Deployment Instructions

## Prerequisites ✅
- [x] VPS with Hostinger
- [x] MongoDB installed
- [x] Domain connected to VPS

## Quick Start (3 Options)

### Option 1: Manual Step-by-Step (Recommended)
Follow `SIMPLE_DEPLOY.md` - it has detailed commands to copy/paste

### Option 2: Automated Script
1. Edit `deploy.sh` - change `DOMAIN="yourdomain.com"` to your actual domain
2. Upload to VPS
3. Run: `chmod +x deploy.sh && sudo ./deploy.sh`

### Option 3: Detailed Guide
Follow `DEPLOY_NOW.md` for comprehensive instructions

## Essential Commands

```bash
# Connect to VPS
ssh root@your-vps-ip

# After setup, these are your daily commands:
pm2 status              # Check backend
pm2 logs x-fin-backend  # View logs
pm2 restart x-fin-backend  # Restart
```

## Files to Edit Before Deployment

1. **deploy.sh** - Line 19: Change domain name
2. **backend/.env** - Add your MongoDB URI and admin password
3. **Nginx config** - Replace `yourdomain.com` with your domain

## Need Help?

1. Check `DEPLOY_NOW.md` for detailed troubleshooting
2. Check `MONGODB_SETUP.md` for MongoDB issues
3. Review logs: `pm2 logs x-fin-backend`

---

**Start with `SIMPLE_DEPLOY.md` for easiest deployment!**

