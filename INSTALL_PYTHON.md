# Installing Python 3.11 on VPS

If you get "Unable to locate package python3.11", follow these steps:

## Option 1: Check Available Python Version (Easiest)

First, check what Python version is already available:

```bash
python3 --version
```

If it shows Python 3.9, 3.10, or 3.11, you can use that! Just adjust the commands.

**If Python 3.10 or higher is available, use this instead:**

```bash
# Install available Python version
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev

# Verify version
python3 --version
```

Then in all commands, replace `python3.11` with `python3` or `python3.10` (whatever version you have).

---

## Option 2: Install Python 3.11 from deadsnakes PPA (Ubuntu)

```bash
# Add deadsnakes PPA
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verify installation
python3.11 --version
```

---

## Option 3: Install Python 3.11 from Source (If PPA doesn't work)

```bash
# Install build dependencies
sudo apt update
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev

# Download Python 3.11
cd /tmp
wget https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9

# Configure and build
./configure --enable-optimizations
make -j$(nproc)
sudo make altinstall

# Verify
python3.11 --version
```

---

## Quick Fix: Use Available Python Version

**Most likely, your VPS already has Python 3.9 or 3.10. Let's check and use that:**

```bash
# Check Python version
python3 --version

# Install Python packages (use whatever version you have)
sudo apt update
sudo apt install -y python3 python3-venv python3-pip python3-dev

# Verify
python3 --version
pip3 --version
```

Then update your commands:
- Replace `python3.11` with `python3`
- Replace `python3.11-venv` with `python3-venv`

---

## Update ecosystem.config.js

If you're using a different Python version, edit the PM2 config:

```bash
cd /var/www/x-fin-dataset/backend
nano ecosystem.config.js
```

Change line 5 from:
```javascript
interpreter: 'python3.11',
```

To:
```javascript
interpreter: 'python3',  // or python3.10, python3.9, etc.
```

---

## Recommended: Check First, Then Install

Run this to see what's available:

```bash
# Check available Python versions
apt-cache search python3 | grep -E "^python3[0-9]"

# Check what's installed
python3 --version
which python3
```

Then use the appropriate version for your system!

