# VPS Deployment Guide

## Prerequisites

1. **Python 3.11+** installed
2. **Node.js & npm** installed
3. **MongoDB** running and accessible
4. **PM2** installed globally (`npm install -g pm2`)
5. **Nginx** (optional, for reverse proxy)

## Step 1: Backend Configuration

### 1.1 Create `.env` file in `backend/` directory

```bash
cd backend
cp env.sample .env
nano .env
```

### 1.2 Required Environment Variables

```env
# ==== MongoDB Configuration ====
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=nse_data
MONGO_USERNAME=your_mongo_username
MONGO_PASSWORD=your_mongo_password

# ==== Flask / API Configuration ====
FLASK_ENV=production
FLASK_DEBUG=False
HOST=0.0.0.0
PORT=5000

# ==== JWT Authentication ====
# Generate a secure key: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-generated-secret-key-min-32-chars

# ==== Admin Credentials ====
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# ==== CORS Configuration (IMPORTANT for Production) ====
# Add your frontend domain(s)
CORS_ORIGINS=https://your-domain.com,https://admin.your-domain.com

# ==== Auto-start Schedulers ====
AUTO_START_SCHEDULERS=true

# ==== Logging (Optional) ====
LOG_FILE=logs/app.log
LOG_LEVEL=INFO
```

### 1.3 Update PM2 Configuration

Edit `backend/ecosystem.config.js`:

```javascript
module.exports = {
  apps: [{
    name: 'x-fin-backend',
    script: 'admin_panel.py',
    interpreter: 'python3',  // or 'python3.11'
    cwd: '/path/to/your/backend',  // UPDATE THIS PATH
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      FLASK_ENV: 'production',
      PORT: 5000,
      AUTO_START_SCHEDULERS: 'true'
    },
    error_file: './logs/backend-error.log',
    out_file: './logs/backend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};
```

## Step 2: Frontend Configuration

### 2.1 Update API URL in `frontend-admin/src/config.js`

```javascript
// Update the production URL to match your VPS
export const API_BASE = isDevelopment 
  ? '/api'
  : 'https://api.your-domain.com/api'  // UPDATE THIS
```

### 2.2 Build Frontend

```bash
cd frontend-admin
npm install
npm run build
```

The `dist/` folder contains the production build.

## Step 3: Install Dependencies

### 3.1 Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3.2 Create Logs Directory

```bash
mkdir -p logs
```

## Step 4: Start with PM2

### 4.1 Start Backend

```bash
cd backend
pm2 start ecosystem.config.js
pm2 save
```

### 4.2 Setup PM2 Auto-start (Important!)

```bash
pm2 startup systemd
# Follow the instructions shown
pm2 save
```

### 4.3 Check Status

```bash
pm2 status
pm2 logs x-fin-backend
```

## Step 5: Verify Schedulers

### 5.1 Check Scheduler Status

After starting, check logs to verify all schedulers started:

```bash
pm2 logs x-fin-backend --lines 100
```

You should see:
```
Auto-starting all schedulers...
Starting FII/DII Data Collector...
Starting All Indices Option Chain Collector...
Starting All Banks Option Chain Collector...
Starting All Gainers/Losers Collector...
Starting News Collector...
Starting LiveMint News Collector...
Active scheduler threads: 6/6
```

### 5.2 Verify via API

```bash
curl -X POST http://localhost:5000/api/schedulers/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Step 6: Nginx Configuration (Recommended)

Create `/etc/nginx/sites-available/x-fin-api`:

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    location / {
        proxy_pass http://localhost:5000;
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
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/x-fin-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: SSL Certificate (Recommended)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

## Step 8: Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MongoDB (if remote)
sudo ufw allow 27017/tcp

# Enable firewall
sudo ufw enable
```

## Step 9: Monitoring & Maintenance

### 9.1 Check PM2 Status

```bash
pm2 status
pm2 monit
```

### 9.2 View Logs

```bash
# All logs
pm2 logs x-fin-backend

# Error logs only
pm2 logs x-fin-backend --err

# Last 100 lines
pm2 logs x-fin-backend --lines 100
```

### 9.3 Restart Services

```bash
pm2 restart x-fin-backend
pm2 reload x-fin-backend  # Zero-downtime reload
```

## Step 10: Troubleshooting

### Schedulers Not Starting

1. Check logs: `pm2 logs x-fin-backend`
2. Verify `.env` has `AUTO_START_SCHEDULERS=true`
3. Check Python path in `ecosystem.config.js`
4. Verify all scheduler files exist in `backend/` directory

### MongoDB Connection Issues

1. Verify MongoDB is running: `sudo systemctl status mongod`
2. Check connection string in `.env`
3. Test connection: `python3 -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017').admin.command('ping')"`

### CORS Errors

1. Update `CORS_ORIGINS` in `.env` with your frontend domain
2. Restart backend: `pm2 restart x-fin-backend`

## Security Checklist

- [ ] Changed `JWT_SECRET_KEY` to a strong random value
- [ ] Changed `ADMIN_PASSWORD` to a secure password
- [ ] Set `CORS_ORIGINS` to your actual frontend domain(s)
- [ ] MongoDB has authentication enabled
- [ ] Firewall configured properly
- [ ] SSL certificate installed (HTTPS)
- [ ] Logs directory has proper permissions
- [ ] `.env` file has restricted permissions: `chmod 600 .env`

## Quick Commands Reference

```bash
# Start backend
pm2 start ecosystem.config.js

# Stop backend
pm2 stop x-fin-backend

# Restart backend
pm2 restart x-fin-backend

# View logs
pm2 logs x-fin-backend

# Check status
pm2 status

# Save PM2 configuration
pm2 save

# Delete from PM2
pm2 delete x-fin-backend
```

## Important Notes

1. **Schedulers Auto-start**: Make sure `AUTO_START_SCHEDULERS=true` in `.env` or PM2 config
2. **Working Directory**: Update `cwd` in `ecosystem.config.js` to your actual backend path
3. **Python Version**: Ensure PM2 uses the correct Python interpreter
4. **Logs**: Check `logs/` directory for detailed error messages
5. **Port**: Ensure port 5000 (or your configured port) is not blocked by firewall

