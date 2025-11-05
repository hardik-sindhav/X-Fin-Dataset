# Hostinger VPS Deployment Guide

Complete guide to deploy your X Fin Dataset project on Hostinger VPS hosting.

## Project Structure
- **Backend**: Python Flask API (port 5000)
- **Frontend**: React/Vite application
- **Admin**: React admin panel (same frontend codebase)

---

## Prerequisites

1. **VPS Access**: SSH access to your Hostinger VPS
2. **Domain**: Your domain name pointing to VPS IP
3. **MongoDB**: Either MongoDB Atlas (cloud) or MongoDB installed on VPS

---

## Step 1: Connect to VPS via SSH

```bash
ssh root@your-vps-ip
# or
ssh username@your-vps-ip
```

---

## Step 2: Initial Server Setup

### Update system packages
```bash
sudo apt update
sudo apt upgrade -y
```

### Install essential tools
```bash
sudo apt install -y git curl wget build-essential software-properties-common
```

---

## Step 3: Install Python 3.11+

```bash
# Install Python 3.11 and pip
sudo apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Verify installation
python3.11 --version
pip3 --version
```

---

## Step 4: Install Node.js and npm

```bash
# Install Node.js 18.x LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installation
node --version
npm --version
```

---

## Step 5: Install MongoDB

### Option A: MongoDB Atlas (Recommended - Cloud)
Skip this step if using MongoDB Atlas. Just note your connection string.

### Option B: Install MongoDB on VPS
```bash
# Import MongoDB GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Update and install
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify MongoDB is running
sudo systemctl status mongod
```

---

## Step 6: Install Nginx

```bash
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

---

## Step 7: Install PM2 (Process Manager)

```bash
# Install PM2 globally
sudo npm install -g pm2

# Configure PM2 to start on boot
pm2 startup
# Follow the command output to complete setup
```

---

## Step 8: Setup Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Step 9: Clone/Upload Your Project

### Option A: Using Git
```bash
cd /var/www
sudo git clone your-repository-url x-fin-dataset
sudo chown -R $USER:$USER /var/www/x-fin-dataset
```

### Option B: Using SCP (from local machine)
```bash
# From your local machine
scp -r "C:\Users\HP\Desktop\X Fin Dataset" root@your-vps-ip:/var/www/x-fin-dataset
```

### Option C: Using FileZilla/SFTP
Upload your project folder to `/var/www/x-fin-dataset`

---

## Step 10: Setup Backend

```bash
cd /var/www/x-fin-dataset/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

### Add to .env file:
```env
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/nse_data
# OR if using MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/nse_data?retryWrites=true&w=majority

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# JWT Secret (generate a strong random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Admin Credentials (change these!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=your-hashed-password-here

# Server Configuration
HOST=127.0.0.1
PORT=5000
```

### Generate password hash:
```bash
python3.11 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

### Test backend
```bash
# Test if backend runs
python3.11 admin_panel.py
# Press Ctrl+C to stop
```

---

## Step 11: Create PM2 Config for Backend

```bash
cd /var/www/x-fin-dataset/backend
nano ecosystem.config.js
```

### Add this content:
```javascript
module.exports = {
  apps: [{
    name: 'x-fin-backend',
    script: 'admin_panel.py',
    interpreter: 'python3.11',
    cwd: '/var/www/x-fin-dataset/backend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      FLASK_ENV: 'production',
      PORT: 5000
    },
    error_file: './logs/backend-error.log',
    out_file: './logs/backend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};
```

### Start backend with PM2
```bash
# Create logs directory
mkdir -p logs

# Start backend
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Check status
pm2 status
pm2 logs x-fin-backend
```

---

## Step 12: Build Frontend

```bash
cd /var/www/x-fin-dataset/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify build
ls -la dist/
```

---

## Step 13: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/x-fin-dataset
```

### Add this configuration:
```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;  # Change to your domain

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# Frontend Application
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;  # Change to your domain

    root /var/www/x-fin-dataset/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Step 14: Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com

# Auto-renewal setup
sudo certbot renew --dry-run
```

---

## Step 15: Update Frontend API Base URL

If your frontend uses `/api` as base URL, it should work with the Nginx proxy. If it uses a hardcoded URL, update it:

```bash
cd /var/www/x-fin-dataset/frontend/src
nano App.jsx
# Change API_BASE from '/api' to 'https://api.yourdomain.com/api' if needed
# Or keep it as '/api' if using same domain
```

Rebuild frontend:
```bash
cd /var/www/x-fin-dataset/frontend
npm run build
```

---

## Step 16: Start All Schedulers

The backend should start schedulers automatically. To verify:

```bash
# Check PM2 logs
pm2 logs x-fin-backend

# Check if schedulers are running
pm2 list

# Monitor resources
pm2 monit
```

---

## Step 17: Create Systemd Service (Optional - Alternative to PM2)

If you prefer systemd instead of PM2:

```bash
sudo nano /etc/systemd/system/x-fin-backend.service
```

### Add this content:
```ini
[Unit]
Description=X Fin Dataset Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/x-fin-dataset/backend
Environment="PATH=/var/www/x-fin-dataset/backend/venv/bin"
ExecStart=/var/www/x-fin-dataset/backend/venv/bin/python3.11 admin_panel.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable x-fin-backend
sudo systemctl start x-fin-backend
sudo systemctl status x-fin-backend
```

---

## Step 18: Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/x-fin-dataset
```

### Add this content:
```conf
/var/www/x-fin-dataset/backend/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        pm2 reloadLogs
    endscript
}
```

---

## Step 19: Security Hardening

### 1. Update MongoDB to require authentication (if using local MongoDB)
```bash
# Edit MongoDB config
sudo nano /etc/mongod.conf

# Add security section:
security:
  authorization: enabled

# Restart MongoDB
sudo systemctl restart mongod

# Create admin user
mongosh
use admin
db.createUser({
  user: "admin",
  pwd: "your-secure-password",
  roles: [ { role: "root", db: "admin" } ]
})
```

### 2. Update .env with authenticated MongoDB URI
```env
MONGODB_URI=mongodb://admin:password@localhost:27017/nse_data?authSource=admin
```

### 3. Set proper file permissions
```bash
sudo chown -R www-data:www-data /var/www/x-fin-dataset
sudo chmod -R 755 /var/www/x-fin-dataset
sudo chmod -R 600 /var/www/x-fin-dataset/backend/.env
```

---

## Step 20: Monitoring and Maintenance

### Check services status
```bash
# Backend
pm2 status
pm2 logs x-fin-backend --lines 50

# Nginx
sudo systemctl status nginx

# MongoDB (if local)
sudo systemctl status mongod

# Disk space
df -h

# Memory usage
free -h
```

### Useful PM2 commands
```bash
pm2 restart x-fin-backend    # Restart backend
pm2 stop x-fin-backend       # Stop backend
pm2 start x-fin-backend      # Start backend
pm2 logs x-fin-backend       # View logs
pm2 monit                     # Monitor resources
```

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
pm2 logs x-fin-backend --err

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000

# Test backend manually
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3.11 admin_panel.py
```

### Nginx errors
```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### MongoDB connection issues
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
mongosh "mongodb://localhost:27017"
```

### Frontend not loading
```bash
# Check if build exists
ls -la /var/www/x-fin-dataset/frontend/dist

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Rebuild frontend
cd /var/www/x-fin-dataset/frontend
npm run build
```

---

## Quick Reference Commands

```bash
# Restart all services
pm2 restart x-fin-backend
sudo systemctl restart nginx

# View logs
pm2 logs x-fin-backend
sudo tail -f /var/log/nginx/error.log

# Update project
cd /var/www/x-fin-dataset
git pull  # if using git
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
pm2 restart x-fin-backend

# Backup MongoDB (if local)
mongodump --out /backup/mongodb-$(date +%Y%m%d)
```

---

## Domain DNS Configuration

Point your domains to your VPS IP:

```
A Record: yourdomain.com -> VPS_IP
A Record: www.yourdomain.com -> VPS_IP
A Record: api.yourdomain.com -> VPS_IP
```

---

## Estimated Resource Requirements

- **CPU**: 2+ cores
- **RAM**: 2GB+ (4GB recommended)
- **Storage**: 20GB+ (for logs and data)
- **Bandwidth**: Depends on usage

---

## Support

For Hostinger-specific issues, check:
- Hostinger VPS documentation
- Hostinger support ticket system

---

**Congratulations! Your application should now be live!** 🎉

Access your application at:
- Frontend: `https://yourdomain.com`
- API: `https://api.yourdomain.com`
- Admin Panel: `https://yourdomain.com` (same as frontend, login required)

