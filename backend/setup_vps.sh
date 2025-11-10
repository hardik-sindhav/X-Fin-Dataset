#!/bin/bash

# VPS Setup Script for X Fin Dataset Backend
# This script helps set up the backend on a VPS

set -e

echo "=========================================="
echo "X Fin Dataset - VPS Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${YELLOW}Warning: Running as root. Consider using a regular user.${NC}"
fi

# Step 1: Check Python
echo -e "${GREEN}Step 1: Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python found: $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

# Step 2: Check Node.js and PM2
echo -e "${GREEN}Step 2: Checking Node.js and PM2...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js found: $NODE_VERSION"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js${NC}"
    exit 1
fi

if command -v pm2 &> /dev/null; then
    PM2_VERSION=$(pm2 --version)
    echo "✓ PM2 found: v$PM2_VERSION"
else
    echo -e "${YELLOW}PM2 not found. Installing...${NC}"
    npm install -g pm2
    echo "✓ PM2 installed"
fi

# Step 3: Create virtual environment
echo -e "${GREEN}Step 3: Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Step 4: Install dependencies
echo -e "${GREEN}Step 4: Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✓ Dependencies installed"

# Step 5: Create logs directory
echo -e "${GREEN}Step 5: Creating logs directory...${NC}"
mkdir -p logs
echo "✓ Logs directory created"

# Step 6: Check .env file
echo -e "${GREEN}Step 6: Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}.env file not found!${NC}"
    echo "Creating .env from env.sample..."
    if [ -f "env.sample" ]; then
        cp env.sample .env
        echo "✓ .env file created from template"
        echo -e "${YELLOW}⚠ IMPORTANT: Please edit .env file with your actual values!${NC}"
        echo "   Run: nano .env"
    else
        echo -e "${RED}✗ env.sample not found${NC}"
    fi
else
    echo "✓ .env file exists"
    # Check if critical values are set
    if grep -q "your-secret-key-change-in-production" .env || grep -q "your_secure_password_here" .env; then
        echo -e "${YELLOW}⚠ WARNING: .env file contains default/placeholder values!${NC}"
        echo "   Please update JWT_SECRET_KEY and ADMIN_PASSWORD"
    fi
fi

# Step 7: Update ecosystem.config.js
echo -e "${GREEN}Step 7: Checking PM2 configuration...${NC}"
CURRENT_DIR=$(pwd)
if grep -q "/var/www/x-fin-dataset/backend" ecosystem.config.js; then
    echo -e "${YELLOW}⚠ Please update 'cwd' path in ecosystem.config.js${NC}"
    echo "   Current directory: $CURRENT_DIR"
    echo "   Update line 6 in ecosystem.config.js to: cwd: '$CURRENT_DIR'"
fi

# Step 8: Check MongoDB connection
echo -e "${GREEN}Step 8: Testing MongoDB connection...${NC}"
if python3 -c "from pymongo import MongoClient; import os; from dotenv import load_dotenv; load_dotenv(); host=os.getenv('MONGO_HOST', 'localhost'); port=int(os.getenv('MONGO_PORT', 27017)); MongoClient(host, port).admin.command('ping')" 2>/dev/null; then
    echo "✓ MongoDB connection successful"
else
    echo -e "${YELLOW}⚠ MongoDB connection test failed${NC}"
    echo "   Please check your MongoDB settings in .env"
fi

# Step 9: Generate JWT secret if needed
echo -e "${GREEN}Step 9: Checking JWT secret...${NC}"
if grep -q "your-secret-key-change-in-production" .env 2>/dev/null; then
    echo -e "${YELLOW}Generating secure JWT secret...${NC}"
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    if command -v sed &> /dev/null; then
        sed -i "s/JWT_SECRET_KEY=your-secret-key-change-in-production-min-32-chars/JWT_SECRET_KEY=$NEW_SECRET/" .env
        echo "✓ JWT secret generated and updated in .env"
    else
        echo "Generated secret: $NEW_SECRET"
        echo "Please update JWT_SECRET_KEY in .env manually"
    fi
else
    echo "✓ JWT secret appears to be set"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your actual values:"
echo "   nano .env"
echo ""
echo "2. Update ecosystem.config.js with correct path:"
echo "   nano ecosystem.config.js"
echo ""
echo "3. Start the backend with PM2:"
echo "   pm2 start ecosystem.config.js"
echo "   pm2 save"
echo ""
echo "4. Setup PM2 auto-start:"
echo "   pm2 startup systemd"
echo "   (Follow the instructions shown)"
echo ""
echo "5. Check logs to verify schedulers started:"
echo "   pm2 logs x-fin-backend --lines 50"
echo ""
echo "6. Verify all 6 schedulers are running:"
echo "   Look for: 'Active scheduler threads: 6/6'"
echo ""

