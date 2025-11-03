#!/bin/bash
# Linux/Mac Shell Script to Start All Schedulers
# This script starts all data collectors automatically

echo "============================================"
echo "Starting X Fin Data Collectors"
echo "============================================"

# Get the directory where the script is located
cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed or not in PATH"
    echo "Please install Python 3.7+"
    exit 1
fi

# Start the master scheduler
echo "Starting all schedulers..."
python3 start_all_schedulers.py

