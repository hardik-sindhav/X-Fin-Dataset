# 🚀 Deployment Guide for Your VPS

## Your VPS Details
- **IP Address**: 147.93.97.60
- **Username**: root
- **Hostname**: srv1107349.hstgr.cloud

---

## Step 1: Connect to Your VPS

```bash
ssh root@147.93.97.60
```

---

## Step 2: Install Required Software

```bash
# Update system
apt update && apt upgrade -y

# Install Python (check what's available)
python3 --version

# Install Python packages
apt install -y python3 python3-venv python3-pip python3-dev

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Nginx
apt install -y nginx

# Install PM2
npm install -g pm2

# Install Git (if not installed)
apt install -y git
```

---

## Step 3: Create Project Directory

```bash
mkdir -p /var/www/x-fin-dataset
cd /var/www/x-fin-dataset
```

---

## Step 4: Upload Your Project

**Option A: Using SCP (from your Windows computer)**

Open PowerShell on your Windows machine:

```powershell
cd "C:\Users\HP\Desktop\X Fin Dataset"
scp -r * root@147.93.97.60:/var/www/x-fin-dataset/
```

**Option B: Using Git (if you have GitHub repo)**

On VPS:
```bash
cd /var/www/x-fin-dataset
git clone https://github.com/yourusername/your-repo.git .
```

---

## Step 5: Setup Backend

```bash
cd /var/www/x-fin-dataset/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create .env file
nano .env
```

**Paste this in .env (replace password hash):**
```env
MONGODB_URI=mongodb://localhost:27017/nse_data
FLASK_ENV=production
FLASK_DEBUG=False
JWT_SECRET_KEY=change-this-to-random-string-123456789
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$abc123$your-hash-here
HOST=127.0.0.1
PORT=5000
```

**Generate password hash:**
```bash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
```

**Test MongoDB:**
```bash
python3 test_mongodb.py
```

---

## Step 6: Start Backend

```bash
cd /var/www/x-fin-dataset/backend

# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 config
pm2 save

# Setup auto-start
pm2 startup
# Copy and run the command it shows

# Check status
pm2 status
pm2 logs x-fin-backend --lines 20
```

---

## Step 7: Build Frontend

```bash
cd /var/www/x-fin-dataset/frontend

# Install dependencies
npm install

# Build
npm run build

# Verify
ls -la dist/
```

---

## Step 8: Configure Nginx

```bash
# Create config
nano /etc/nginx/sites-available/x-fin-dataset
```

**Paste this (replace `yourdomain.com` with your actual domain):**
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    root /var/www/x-fin-dataset/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Enable site:**
```bash
ln -s /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

---

## Step 9: Setup SSL

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## Step 10: Test

Visit: `http://147.93.97.60` or `https://yourdomain.com`

---

## Quick Commands

```bash
# Check backend
pm2 status
pm2 logs x-fin-backend

# Restart backend
pm2 restart x-fin-backend

# Check Nginx
systemctl status nginx

# Check MongoDB
systemctl status mongod
```

---

**Your VPS is ready! 🎉**

