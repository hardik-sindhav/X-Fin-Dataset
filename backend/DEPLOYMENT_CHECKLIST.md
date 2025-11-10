# VPS Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Environment Variables (.env file)
- [ ] `MONGO_HOST` - MongoDB host (localhost or remote)
- [ ] `MONGO_PORT` - MongoDB port (default: 27017)
- [ ] `MONGO_DB_NAME` - Database name
- [ ] `MONGO_USERNAME` - MongoDB username (if auth enabled)
- [ ] `MONGO_PASSWORD` - MongoDB password (if auth enabled)
- [ ] `JWT_SECRET_KEY` - Strong random secret (min 32 chars)
- [ ] `ADMIN_USERNAME` - Admin login username
- [ ] `ADMIN_PASSWORD` - Admin login password
- [ ] `CORS_ORIGINS` - Your frontend domain(s) - **REQUIRED**
- [ ] `AUTO_START_SCHEDULERS=true` - Enable auto-start
- [ ] `FLASK_ENV=production`
- [ ] `FLASK_DEBUG=False`

### 2. PM2 Configuration (ecosystem.config.js)
- [ ] Update `cwd` path to your actual backend directory
- [ ] Verify `interpreter` (python3 or python3.11)
- [ ] Check `AUTO_START_SCHEDULERS: 'true'` in env section

### 3. Frontend Configuration
- [ ] Update `frontend-admin/src/config.js` with your API URL
- [ ] Build frontend: `npm run build`
- [ ] Deploy `dist/` folder to web server

### 4. System Requirements
- [ ] Python 3.11+ installed
- [ ] Node.js & npm installed
- [ ] PM2 installed globally: `npm install -g pm2`
- [ ] MongoDB running and accessible
- [ ] Virtual environment created: `python3 -m venv venv`
- [ ] Dependencies installed: `pip install -r requirements.txt`

### 5. Directory Structure
- [ ] `logs/` directory created
- [ ] Proper file permissions set
- [ ] `.env` file has restricted permissions: `chmod 600 .env`

## 🚀 Deployment Steps

### Step 1: Setup Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
mkdir -p logs
```

### Step 2: Configure Environment
```bash
cp env.sample .env
nano .env  # Edit with your values
chmod 600 .env  # Secure the file
```

### Step 3: Update PM2 Config
```bash
nano ecosystem.config.js
# Update cwd path to your actual directory
```

### Step 4: Start with PM2
```bash
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd  # Follow instructions
```

### Step 5: Verify Schedulers
```bash
pm2 logs x-fin-backend --lines 50
# Look for: "Active scheduler threads: 6/6"
```

## 🔍 Verification

### Check Backend Status
```bash
pm2 status
pm2 logs x-fin-backend
```

### Test API
```bash
curl http://localhost:5000/api/mongodb/health
```

### Check Schedulers
```bash
# View scheduler startup logs
pm2 logs x-fin-backend | grep -i scheduler
```

## ⚠️ Common Issues

### Schedulers Not Starting
1. Check `.env` has `AUTO_START_SCHEDULERS=true`
2. Check PM2 logs: `pm2 logs x-fin-backend`
3. Verify Python path in ecosystem.config.js
4. Check all scheduler files exist

### MongoDB Connection Failed
1. Verify MongoDB is running: `sudo systemctl status mongod`
2. Check connection details in `.env`
3. Test: `mongo --host localhost --port 27017`

### CORS Errors
1. Update `CORS_ORIGINS` in `.env` with frontend domain
2. Restart: `pm2 restart x-fin-backend`

### Port Already in Use
1. Check: `sudo lsof -i :5000`
2. Kill process or change PORT in `.env`

## 📝 Post-Deployment

- [ ] All 6 schedulers running (check logs)
- [ ] API accessible from frontend
- [ ] MongoDB connection working
- [ ] Logs directory has write permissions
- [ ] PM2 auto-start configured
- [ ] Firewall rules set
- [ ] SSL certificate installed (if using HTTPS)

