# Simple Deployment Guide - Follow These Steps

## What You Need
- Your VPS IP address
- Your domain name
- SSH access to VPS

---

## Step 1: Connect to Your VPS

Open terminal/command prompt and run:
```bash
ssh root@your-vps-ip
# Enter your password when prompted
```

---

## Step 2: Install Required Software

Copy and paste these commands one by one:

```bash
# Update system
apt update && apt upgrade -y

# Install Python (check what's available first)
python3 --version

# If Python 3.9+ is available, use this:
apt install -y python3 python3-venv python3-pip python3-dev

# OR if you want Python 3.11 specifically, use this:
# apt install -y software-properties-common
# add-apt-repository ppa:deadsnakes/ppa -y
# apt update
# apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Nginx
apt install -y nginx

# Install PM2
npm install -g pm2
```

---

## Step 3: Create Project Directory

```bash
mkdir -p /var/www/x-fin-dataset
cd /var/www/x-fin-dataset
```

---

## Step 4: Upload Your Project Files

**Option A: Using SCP (from your local Windows machine)**

Open a NEW terminal/command prompt on your Windows computer (keep SSH session open):

```powershell
cd "C:\Users\HP\Desktop\X Fin Dataset"
scp -r * root@your-vps-ip:/var/www/x-fin-dataset/
```

**Option B: Using FileZilla**
1. Download FileZilla
2. Connect via SFTP to your VPS
3. Upload entire project folder to `/var/www/x-fin-dataset`

---

## Step 5: Setup Backend

Go back to your SSH session and run:

```bash
cd /var/www/x-fin-dataset/backend

# Create virtual environment (use python3 if python3.11 not available)
python3 -m venv venv
# OR if you installed python3.11: python3.11 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

**In the nano editor, paste this (then press Ctrl+X, then Y, then Enter to save):**

```env
MONGODB_URI=mongodb://localhost:27017/nse_data
FLASK_ENV=production
FLASK_DEBUG=False
JWT_SECRET_KEY=change-this-to-random-string-123456789
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$abc123$def456
HOST=127.0.0.1
PORT=5000
```

**Generate a password hash:**
```bash
# Use python3 if python3.11 not available
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
# OR if you have python3.11: python3.11 -c "..."
```
Copy the output and replace `ADMIN_PASSWORD_HASH` in .env

**Test MongoDB:**
```bash
# Use python3 if python3.11 not available
python3 test_mongodb.py
# OR if you have python3.11: python3.11 test_mongodb.py
```

---

## Step 6: Start Backend

```bash
cd /var/www/x-fin-dataset/backend

# Create logs folder
mkdir -p logs

# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 config
pm2 save

# Setup auto-start
pm2 startup
# Copy and run the command it shows you
```

---

## Step 7: Build Frontend

```bash
cd /var/www/x-fin-dataset/frontend

# Install dependencies
npm install

# Build
npm run build
```

---

## Step 8: Configure Nginx

```bash
# Create config file
nano /etc/nginx/sites-available/x-fin-dataset
```

**Paste this (REPLACE `yourdomain.com` with YOUR actual domain):**

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

**Save (Ctrl+X, Y, Enter)**

**Enable site:**
```bash
ln -s /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

---

## Step 9: Setup SSL (HTTPS)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow the prompts (enter email, agree to terms, choose redirect HTTP to HTTPS)

---

## Step 10: Test Your Site

Open browser and visit: `https://yourdomain.com`

You should see your application!

---

## Quick Commands

```bash
# Check backend status
pm2 status

# View backend logs
pm2 logs x-fin-backend

# Restart backend
pm2 restart x-fin-backend

# Check Nginx
systemctl status nginx

# Check MongoDB
systemctl status mongod
```

---

## If Something Goes Wrong

**Backend not working?**
```bash
pm2 logs x-fin-backend --err
pm2 restart x-fin-backend
```

**Nginx errors?**
```bash
nginx -t
tail -f /var/log/nginx/error.log
```

**Can't access website?**
```bash
# Check if services are running
pm2 status
systemctl status nginx
systemctl status mongod
```

---

**That's it! Your application should be live! 🎉**

