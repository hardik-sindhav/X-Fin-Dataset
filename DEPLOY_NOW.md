# Complete Deployment Guide - Step by Step

Follow these steps in order to deploy your project on your VPS.

## Prerequisites Checklist
- [x] VPS with Hostinger
- [x] MongoDB installed on VPS
- [x] Domain connected to VPS IP
- [ ] SSH access to VPS

---

## Step 1: Connect to Your VPS

```bash
ssh root@your-vps-ip
# or
ssh username@your-vps-ip
```

---

## Step 2: Install Required Software

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
sudo apt install -y nginx

# Install PM2 (Process Manager)
sudo npm install -g pm2

# Install Git (if not installed)
sudo apt install -y git

# Verify installations
python3.11 --version
node --version
npm --version
nginx -v
pm2 --version
```

---

## Step 3: Upload Your Project to VPS

### Option A: Using SCP from Your Local Machine (Windows)

Open PowerShell or CMD on your local machine:

```powershell
# Navigate to your project directory
cd "C:\Users\HP\Desktop\X Fin Dataset"

# Upload entire project (replace with your VPS IP and username)
scp -r * root@your-vps-ip:/var/www/x-fin-dataset/
```

### Option B: Using Git (if your project is on GitHub/GitLab)

On your VPS:
```bash
cd /var/www
sudo git clone your-repository-url x-fin-dataset
sudo chown -R $USER:$USER x-fin-dataset
```

### Option C: Using FileZilla/SFTP

1. Download FileZilla (if you don't have it)
2. Connect to your VPS using SFTP
3. Upload your project folder to `/var/www/x-fin-dataset`

---

## Step 4: Set Proper Permissions

```bash
cd /var/www/x-fin-dataset
sudo chown -R $USER:$USER .
sudo chmod -R 755 .
```

---

## Step 5: Setup Backend

```bash
cd /var/www/x-fin-dataset/backend

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

# Create .env file
nano .env
```

**Add this to .env file (replace with your actual values):**
```env
# MongoDB Connection (since you installed MongoDB on VPS)
MONGODB_URI=mongodb://localhost:27017/nse_data

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# JWT Secret Key (generate a random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production-123456789

# Admin Credentials
# Generate password hash: python3.11 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password'))"
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=pbkdf2:sha256:600000$...your-hashed-password-here

# Server Configuration
HOST=127.0.0.1
PORT=5000
```

**Generate password hash:**
```bash
python3.11 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your-password-here'))"
```

**Save and exit (Ctrl+X, then Y, then Enter)**

**Test MongoDB connection:**
```bash
python3.11 test_mongodb.py
```

If successful, you'll see: ✓ MongoDB connection test PASSED

---

## Step 6: Start Backend with PM2

```bash
cd /var/www/x-fin-dataset/backend

# Make sure you're in the backend directory
pwd  # Should show: /var/www/x-fin-dataset/backend

# Start backend with PM2
pm2 start ecosystem.config.js

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Copy and run the command it shows you

# Check status
pm2 status
pm2 logs x-fin-backend --lines 50
```

---

## Step 7: Build Frontend

```bash
cd /var/www/x-fin-dataset/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Verify build
ls -la dist/
# You should see index.html and assets folder
```

---

## Step 8: Configure Nginx

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/x-fin-dataset
```

**Paste this configuration (replace `yourdomain.com` with your actual domain):**

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend files
    root /var/www/x-fin-dataset/frontend/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Main location - serve React app
    location / {
        try_files $uri $uri/ /index.html;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    # API proxy - forward to Flask backend
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
        
        # Increase timeout for long-running requests
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static assets caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

**Save and exit (Ctrl+X, then Y, then Enter)**

**Enable the site:**
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# If test passes, reload Nginx
sudo systemctl reload nginx
```

---

## Step 9: Setup SSL Certificate (HTTPS)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Follow the prompts:
# - Enter your email
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)

# Test auto-renewal
sudo certbot renew --dry-run
```

After SSL setup, your site will be accessible at `https://yourdomain.com`

---

## Step 10: Setup Firewall

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

## Step 11: Verify Everything is Working

### Check Backend
```bash
# Check PM2 status
pm2 status

# View logs
pm2 logs x-fin-backend --lines 20

# Test API directly
curl http://localhost:5000/api/status
```

### Check Nginx
```bash
# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Check MongoDB
```bash
# Check MongoDB status
sudo systemctl status mongod

# Test MongoDB connection
mongosh
show dbs
exit
```

### Test in Browser
1. Open your browser
2. Visit: `http://yourdomain.com` (should redirect to HTTPS after SSL setup)
3. Try logging in with your admin credentials

---

## Step 12: Verify Schedulers are Running

```bash
# Check PM2 logs for scheduler activity
pm2 logs x-fin-backend --lines 100

# You should see messages about schedulers starting
# Look for: "All X schedulers started in background"
```

---

## Troubleshooting

### Backend not starting?
```bash
# Check logs
pm2 logs x-fin-backend --err

# Restart backend
pm2 restart x-fin-backend

# Check if port 5000 is in use
sudo netstat -tulpn | grep 5000
```

### Nginx errors?
```bash
# Check configuration
sudo nginx -t

# View error logs
sudo tail -f /var/log/nginx/error.log

# Restart Nginx
sudo systemctl restart nginx
```

### Can't access website?
```bash
# Check if Nginx is running
sudo systemctl status nginx

# Check if domain DNS is pointing to VPS IP
nslookup yourdomain.com

# Check firewall
sudo ufw status
```

### MongoDB connection issues?
```bash
# Test MongoDB connection
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3.11 test_mongodb.py

# Check MongoDB is running
sudo systemctl status mongod
```

---

## Quick Commands Reference

```bash
# Restart backend
pm2 restart x-fin-backend

# View backend logs
pm2 logs x-fin-backend

# Restart Nginx
sudo systemctl restart nginx

# Check all services
pm2 status
sudo systemctl status nginx
sudo systemctl status mongod

# Update project (after making changes)
cd /var/www/x-fin-dataset
# Upload new files or git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart x-fin-backend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

---

## Success Checklist

After deployment, verify:
- [ ] Backend is running (pm2 status shows x-fin-backend as online)
- [ ] Nginx is running (sudo systemctl status nginx)
- [ ] MongoDB is running (sudo systemctl status mongod)
- [ ] Website loads at https://yourdomain.com
- [ ] API is accessible at https://yourdomain.com/api/status
- [ ] Can login to admin panel
- [ ] Schedulers are running (check PM2 logs)

---

## Your Application URLs

- **Frontend**: `https://yourdomain.com`
- **API**: `https://yourdomain.com/api`
- **Admin Login**: `https://yourdomain.com` (use login button)

---

## Next Steps

1. **Change default admin password** in the admin panel
2. **Configure scheduler settings** via Settings page
3. **Add holidays** via Settings page
4. **Monitor logs** regularly: `pm2 logs x-fin-backend`
5. **Set up backups** for MongoDB data

---

**Congratulations! Your application should now be live! 🎉**

If you encounter any issues, check the troubleshooting section or review the logs.

