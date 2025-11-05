# Quick Deployment Steps - Hostinger VPS

## Prerequisites Checklist
- [ ] VPS IP address
- [ ] SSH access credentials
- [ ] Domain name (optional but recommended)
- [ ] MongoDB connection string (Atlas or local)

## Fast Track Deployment (30 minutes)

### 1. Connect to VPS
```bash
ssh root@your-vps-ip
```

### 2. Run One-Command Setup
```bash
# Update system
apt update && apt upgrade -y

# Install essentials
apt install -y python3.11 python3.11-venv python3-pip nodejs npm nginx git

# Install PM2
npm install -g pm2
```

### 3. Upload Project
```bash
# Create directory
mkdir -p /var/www/x-fin-dataset
cd /var/www/x-fin-dataset

# Option A: Clone from Git
git clone your-repo-url .

# Option B: Upload via SCP (from local machine)
# scp -r "C:\Users\HP\Desktop\X Fin Dataset\*" root@your-vps-ip:/var/www/x-fin-dataset/
```

### 4. Setup Backend
```bash
cd /var/www/x-fin-dataset/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
nano .env
```

**Add to .env:**
```env
MONGODB_URI=mongodb://localhost:27017/nse_data
FLASK_ENV=production
FLASK_DEBUG=False
JWT_SECRET_KEY=generate-random-string-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=generate-hash-here
HOST=127.0.0.1
PORT=5000
```

### 5. Start Backend with PM2
```bash
# Create logs directory
mkdir -p logs

# Start with PM2
pm2 start ecosystem.config.js
pm2 save
pm2 startup  # Follow instructions

# Check status
pm2 status
```

### 6. Build Frontend
```bash
cd /var/www/x-fin-dataset/frontend
npm install
npm run build
```

### 7. Configure Nginx
```bash
# Copy config
sudo cp /var/www/x-fin-dataset/nginx-config.conf /etc/nginx/sites-available/x-fin-dataset

# Edit with your domain
sudo nano /etc/nginx/sites-available/x-fin-dataset
# Change: yourdomain.com to your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optional

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### 8. Setup SSL (Optional but Recommended)
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 9. Setup Firewall
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Verify Deployment

1. **Check Backend**: `pm2 logs x-fin-backend`
2. **Check Nginx**: `sudo systemctl status nginx`
3. **Test API**: `curl http://localhost:5000/api/status`
4. **Test Frontend**: Visit `http://your-vps-ip` in browser

## Common Commands

```bash
# Restart backend
pm2 restart x-fin-backend

# View logs
pm2 logs x-fin-backend

# Restart Nginx
sudo systemctl restart nginx

# Update project
cd /var/www/x-fin-dataset
git pull  # or upload new files
cd backend && source venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install && npm run build
pm2 restart x-fin-backend
```

## Troubleshooting

**Backend not starting?**
```bash
pm2 logs x-fin-backend --err
cd /var/www/x-fin-dataset/backend
source venv/bin/activate
python3.11 admin_panel.py  # Test manually
```

**Nginx errors?**
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

**Port 5000 in use?**
```bash
sudo netstat -tulpn | grep 5000
sudo kill -9 <PID>
```

## Next Steps

1. Point your domain DNS to VPS IP
2. Update frontend API URL if needed
3. Configure MongoDB authentication
4. Set up automated backups
5. Monitor logs regularly

For detailed instructions, see `DEPLOYMENT_GUIDE.md`

