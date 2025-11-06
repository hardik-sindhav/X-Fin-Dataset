#!/bin/bash
# Quick deployment script for timezone fix
# Run this on your VPS after uploading the fixed files

echo "=========================================="
echo "Deploying Timezone Fix"
echo "=========================================="

# Navigate to backend directory
cd /var/www/x-fin-dataset/backend || exit 1

# Activate virtual environment
source venv/bin/activate

# Install/update pytz (should already be in requirements.txt)
echo "Installing/updating pytz..."
pip install pytz==2024.1 -q

# Verify timezone_utils can be imported
echo "Verifying timezone_utils module..."
python3 -c "from timezone_utils import now_for_mongo; print('✓ timezone_utils imported successfully')" || {
    echo "✗ Error: timezone_utils import failed"
    exit 1
}

# Restart PM2 backend
echo "Restarting PM2 backend..."
pm2 restart x-fin-backend

# Wait a moment
sleep 3

# Check PM2 status
echo ""
echo "PM2 Status:"
pm2 status

# Show recent logs
echo ""
echo "Recent PM2 logs (checking for scheduler startup):"
pm2 logs x-fin-backend --lines 30 --nostream | grep -i scheduler || echo "No scheduler messages found (check full logs)"

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check scheduler status: python3 check_schedulers_status.py"
echo "2. View full logs: pm2 logs x-fin-backend"
echo "3. Check if schedulers are running: ps aux | grep scheduler"
echo ""

