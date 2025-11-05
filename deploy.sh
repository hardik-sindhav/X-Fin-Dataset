#!/bin/bash

# X Fin Dataset Deployment Script
# Run this script to deploy updates to your VPS

echo "=========================================="
echo "X Fin Dataset Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/var/www/x-fin-dataset"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 failed"
        exit 1
    fi
}

# Step 1: Update backend
echo -e "\n${YELLOW}Step 1: Updating Backend...${NC}"
cd $BACKEND_DIR
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
check_success "Backend dependencies updated"

# Step 2: Update frontend
echo -e "\n${YELLOW}Step 2: Building Frontend...${NC}"
cd $FRONTEND_DIR
npm install
npm run build
check_success "Frontend built successfully"

# Step 3: Restart backend
echo -e "\n${YELLOW}Step 3: Restarting Backend...${NC}"
pm2 restart x-fin-backend
check_success "Backend restarted"

# Step 4: Reload Nginx
echo -e "\n${YELLOW}Step 4: Reloading Nginx...${NC}"
nginx -t && systemctl reload nginx
check_success "Nginx reloaded"

# Step 5: Show status
echo -e "\n${YELLOW}Step 5: Service Status...${NC}"
pm2 status
echo -e "\n${GREEN}Deployment completed successfully!${NC}"
echo "=========================================="

