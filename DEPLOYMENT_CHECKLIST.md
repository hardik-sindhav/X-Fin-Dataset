# Deployment Checklist - Fill This Out

Use this checklist to track your deployment progress.

## Before You Start

- [ ] You have SSH access to your VPS
- [ ] You know your VPS IP address
- [ ] You have your domain name
- [ ] Domain DNS is pointing to your VPS IP
- [ ] MongoDB is installed on VPS

## Domain Information

- **Domain Name**: _________________________
- **VPS IP Address**: _________________________
- **SSH Username**: _________________________
- **SSH Password/Key**: _________________________

## Step-by-Step Checklist

### Preparation
- [ ] Connected to VPS via SSH
- [ ] Updated system packages (`apt update && apt upgrade`)
- [ ] Project files uploaded to `/var/www/x-fin-dataset`

### Software Installation
- [ ] Python 3.11 installed
- [ ] Node.js installed
- [ ] Nginx installed
- [ ] PM2 installed
- [ ] MongoDB verified running

### Backend Setup
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with correct values
- [ ] MongoDB connection tested (`python3.11 test_mongodb.py`)
- [ ] Backend started with PM2 (`pm2 start ecosystem.config.js`)
- [ ] PM2 startup configured (`pm2 startup`)
- [ ] Backend logs checked (`pm2 logs x-fin-backend`)

### Frontend Setup
- [ ] Dependencies installed (`npm install`)
- [ ] Frontend built (`npm run build`)
- [ ] `dist` folder verified

### Nginx Configuration
- [ ] Nginx config created at `/etc/nginx/sites-available/x-fin-dataset`
- [ ] Domain name updated in config
- [ ] Site enabled (`ln -s`)
- [ ] Nginx config tested (`nginx -t`)
- [ ] Nginx reloaded (`systemctl reload nginx`)

### SSL Certificate (HTTPS)
- [ ] Certbot installed
- [ ] SSL certificate obtained (`certbot --nginx`)
- [ ] HTTPS redirect configured
- [ ] SSL auto-renewal tested

### Firewall
- [ ] Port 22 (SSH) allowed
- [ ] Port 80 (HTTP) allowed
- [ ] Port 443 (HTTPS) allowed
- [ ] Firewall enabled

### Verification
- [ ] Backend is running (`pm2 status`)
- [ ] Nginx is running (`systemctl status nginx`)
- [ ] MongoDB is running (`systemctl status mongod`)
- [ ] Website loads at `http://yourdomain.com`
- [ ] Website redirects to HTTPS
- [ ] API accessible at `https://yourdomain.com/api/status`
- [ ] Can login to admin panel
- [ ] Schedulers are running (check PM2 logs)

### Security
- [ ] Changed default admin password
- [ ] JWT_SECRET_KEY changed in .env
- [ ] MongoDB authentication enabled (if needed)
- [ ] Firewall configured correctly

### Final Configuration
- [ ] Scheduler settings configured via Settings page
- [ ] Holidays added via Settings page
- [ ] Tested data collection

## Your Application URLs

- Frontend: `https://_________________________`
- API: `https://_________________________/api`
- Admin Login: `https://_________________________`

## Admin Credentials

- Username: _________________________
- Password: _________________________

## Important Files

- Backend .env: `/var/www/x-fin-dataset/backend/.env`
- Nginx Config: `/etc/nginx/sites-available/x-fin-dataset`
- PM2 Config: `/var/www/x-fin-dataset/backend/ecosystem.config.js`

## Backup Information

- MongoDB Backup Location: _________________________
- Backup Schedule: _________________________

## Notes

_Add any important notes here:_




