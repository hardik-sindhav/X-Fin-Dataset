#!/bin/bash

# Quick Fix: Install Python based on what's available
# This script checks and installs the best available Python version

echo "Checking Python availability..."

# Check if Python 3 is already installed
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "✓ Python $PYTHON_VERSION is already installed"
    
    # Check if it's 3.9 or higher (good enough)
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 9 ]; then
        echo "✓ Python version is sufficient (3.9+)"
        echo ""
        echo "Installing Python packages..."
        sudo apt update
        sudo apt install -y python3 python3-venv python3-pip python3-dev
        echo ""
        echo "✓ Done! Use 'python3' instead of 'python3.11' in commands"
        exit 0
    fi
fi

# Try to install Python 3.11 from deadsnakes PPA
echo "Attempting to install Python 3.11 from deadsnakes PPA..."

sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

if sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip 2>/dev/null; then
    echo "✓ Python 3.11 installed successfully"
    python3.11 --version
else
    echo "⚠ Python 3.11 installation failed, trying alternative..."
    
    # Install default Python 3
    sudo apt install -y python3 python3-venv python3-pip python3-dev
    python3 --version
    echo ""
    echo "✓ Installed default Python 3 (use 'python3' instead of 'python3.11')"
fi

echo ""
echo "Verification:"
python3 --version || python3.11 --version
pip3 --version

