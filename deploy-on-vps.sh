#!/bin/bash

# Deployment script that runs on VPS
# This script is called by GitHub Actions or can be run manually

set -e

PROJECT_DIR="/var/www/x-fin-dataset"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "🚀 Starting deployment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Update backend
echo -e "${YELLOW}📦 Updating backend...${NC}"
cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Create logs directory
mkdir -p logs

echo -e "${GREEN}✓ Backend updated${NC}"

# Update frontend
echo -e "${YELLOW}📦 Building frontend...${NC}"
cd "$FRONTEND_DIR"

# Install dependencies
npm ci --quiet

# Build frontend
npm run build

echo -e "${GREEN}✓ Frontend built${NC}"

# Restart backend with PM2
echo -e "${YELLOW}🔄 Restarting backend...${NC}"
cd "$BACKEND_DIR"

# Stop existing instance if running
pm2 delete x-fin-backend 2>/dev/null || true

# Start backend
pm2 start ecosystem.config.js
pm2 save

echo -e "${GREEN}✓ Backend restarted${NC}"

# Reload Nginx
echo -e "${YELLOW}🔄 Reloading Nginx...${NC}"
sudo systemctl reload nginx

echo -e "${GREEN}✓ Nginx reloaded${NC}"

# Show status
echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Service Status:"
pm2 status
echo ""
echo "Your application should be live!"

