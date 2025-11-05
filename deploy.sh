#!/bin/bash

# Complete Deployment Script for X Fin Dataset
# Run this script on your VPS to deploy everything automatically

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/x-fin-dataset"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
DOMAIN="yourdomain.com"  # CHANGE THIS TO YOUR DOMAIN

echo -e "${BLUE}=========================================="
echo "X Fin Dataset - Complete Deployment"
echo "==========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Step 1: Check if project directory exists
echo -e "${BLUE}Step 1: Checking project directory...${NC}"
if [ ! -d "$PROJECT_DIR" ]; then
    print_error "Project directory not found: $PROJECT_DIR"
    print_info "Please upload your project to $PROJECT_DIR first"
    exit 1
fi
print_status "Project directory exists"

# Step 2: Install system dependencies
echo -e "\n${BLUE}Step 2: Installing system dependencies...${NC}"
apt update -qq
apt install -y python3.11 python3.11-venv python3-pip python3.11-dev nodejs npm nginx git curl wget > /dev/null 2>&1
print_status "System dependencies installed"

# Step 3: Install PM2
echo -e "\n${BLUE}Step 3: Installing PM2...${NC}"
if ! command -v pm2 &> /dev/null; then
    npm install -g pm2 > /dev/null 2>&1
    print_status "PM2 installed"
else
    print_status "PM2 already installed"
fi

# Step 4: Setup Backend
echo -e "\n${BLUE}Step 4: Setting up backend...${NC}"
cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    print_status "Virtual environment created"
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet > /dev/null 2>&1
print_status "Backend dependencies installed"

# Create logs directory
mkdir -p logs
print_status "Logs directory created"

# Check if .env exists
if [ ! -f ".env" ]; then
    print_info ".env file not found. Creating template..."
    cat > .env << EOF
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/nse_data

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# JWT Secret Key (CHANGE THIS!)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Admin Credentials (CHANGE THIS!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$(python3.11 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))")

# Server Configuration
HOST=127.0.0.1
PORT=5000
EOF
    print_info ".env file created. Please edit it with your actual values!"
    print_info "Run: nano $BACKEND_DIR/.env"
else
    print_status ".env file exists"
fi

# Test MongoDB connection
print_info "Testing MongoDB connection..."
if python3.11 test_mongodb.py > /dev/null 2>&1; then
    print_status "MongoDB connection successful"
else
    print_error "MongoDB connection failed. Please check your .env file"
    print_info "Run: python3.11 test_mongodb.py"
fi

# Step 5: Start Backend with PM2
echo -e "\n${BLUE}Step 5: Starting backend with PM2...${NC}"
cd "$BACKEND_DIR"

# Stop existing instance if running
pm2 delete x-fin-backend 2>/dev/null || true

# Start backend
pm2 start ecosystem.config.js
pm2 save
print_status "Backend started with PM2"

# Setup PM2 startup
print_info "Setting up PM2 startup..."
pm2 startup systemd -u $USER --hp $HOME > /tmp/pm2-startup.txt 2>&1 || true
print_info "PM2 startup configured (check /tmp/pm2-startup.txt for manual steps if needed)"

# Step 6: Build Frontend
echo -e "\n${BLUE}Step 6: Building frontend...${NC}"
cd "$FRONTEND_DIR"

# Install dependencies
if [ ! -d "node_modules" ]; then
    npm install --quiet
    print_status "Frontend dependencies installed"
else
    print_status "Frontend dependencies already installed"
fi

# Build
npm run build > /dev/null 2>&1
if [ -d "dist" ]; then
    print_status "Frontend built successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

# Step 7: Configure Nginx
echo -e "\n${BLUE}Step 7: Configuring Nginx...${NC}"

# Create Nginx configuration
cat > /tmp/x-fin-nginx.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    root ${FRONTEND_DIR}/dist;
    index index.html;

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    location / {
        try_files \$uri \$uri/ /index.html;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
EOF

# Copy to Nginx sites-available
cp /tmp/x-fin-nginx.conf /etc/nginx/sites-available/x-fin-dataset

# Enable site
ln -sf /etc/nginx/sites-available/x-fin-dataset /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
if nginx -t > /dev/null 2>&1; then
    systemctl reload nginx
    print_status "Nginx configured and reloaded"
else
    print_error "Nginx configuration test failed"
    nginx -t
    exit 1
fi

# Step 8: Setup Firewall
echo -e "\n${BLUE}Step 8: Setting up firewall...${NC}"
ufw allow 22/tcp > /dev/null 2>&1
ufw allow 80/tcp > /dev/null 2>&1
ufw allow 443/tcp > /dev/null 2>&1
echo "y" | ufw enable > /dev/null 2>&1
print_status "Firewall configured"

# Step 9: Summary
echo -e "\n${GREEN}=========================================="
echo "Deployment Complete!"
echo "==========================================${NC}\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Edit .env file: nano $BACKEND_DIR/.env"
echo "2. Change your domain in Nginx config: nano /etc/nginx/sites-available/x-fin-dataset"
echo "3. Setup SSL: sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
echo "4. Test your site: http://${DOMAIN}"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  pm2 status              - Check backend status"
echo "  pm2 logs x-fin-backend  - View backend logs"
echo "  sudo systemctl status nginx - Check Nginx status"
echo "  sudo systemctl status mongod - Check MongoDB status"
echo ""
echo -e "${GREEN}Your application should be accessible at: http://${DOMAIN}${NC}\n"
