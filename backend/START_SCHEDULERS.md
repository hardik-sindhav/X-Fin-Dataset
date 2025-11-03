# 🚀 How to Run All Cronjobs Automatically

This guide explains how to run all data collectors automatically on your system.

## 📋 Overview

Your application has **16 schedulers** that collect data automatically:

1. **FII/DII Data Collector** - Runs Mon-Fri at 5:00 PM
2. **NIFTY Option Chain Collector** - Runs Mon-Fri 09:15 AM - 03:30 PM (every 3 minutes)
3. **BankNifty Option Chain Collector** - Runs Mon-Fri 09:15 AM - 03:30 PM (every 3 minutes)
4. **News Collector** - Runs Mon-Fri 09:00 AM - 03:30 PM (every 15 minutes)
5. **12 Bank Option Chain Collectors** - Each runs Mon-Fri 09:15 AM - 03:30 PM (every 3 minutes)
   - HDFC Bank, ICICI Bank, SBIN, Kotak Bank, Axis Bank
   - Bank of Baroda, PNB, CANBK, AUBANK, IndusInd Bank
   - IDFC First Bank, Federal Bank

## 🎯 Method 1: Run All Schedulers Together (Recommended)

### Step 1: Run the Master Scheduler Script

```bash
cd backend
python start_all_schedulers.py
```

This will start all 16 schedulers in separate threads automatically.

### Step 2: Keep It Running

Keep the terminal window open. The script will run continuously until you stop it (Ctrl+C).

**For Production:** Use one of the methods below to run it in the background.

---

## 🪟 Method 2: Run as Windows Service (Windows)

### Option A: Using NSSM (Non-Sucking Service Manager)

1. **Download NSSM:**
   - Visit: https://nssm.cc/download
   - Extract the ZIP file

2. **Install as Service:**
   ```cmd
   cd path\to\nssm\win64
   nssm install XFinDataCollectors "C:\Python\python.exe" "C:\Users\HP\Desktop\X Fin Dataset\backend\start_all_schedulers.py"
   nssm set XFinDataCollectors AppDirectory "C:\Users\HP\Desktop\X Fin Dataset\backend"
   nssm set XFinDataCollectors DisplayName "X Fin Data Collectors"
   nssm set XFinDataCollectors Description "Automated data collectors for NSE market data"
   ```

3. **Start the Service:**
   ```cmd
   nssm start XFinDataCollectors
   ```

4. **Check Status:**
   ```cmd
   nssm status XFinDataCollectors
   ```

5. **Stop the Service:**
   ```cmd
   nssm stop XFinDataCollectors
   ```

---

## 🐧 Method 3: Run as Linux Service (Linux/Mac)

### Create a Systemd Service

1. **Create Service File:**
   ```bash
   sudo nano /etc/systemd/system/xfin-collectors.service
   ```

2. **Add Configuration:**
   ```ini
   [Unit]
   Description=X Fin Data Collectors
   After=network.target mongodb.service

   [Service]
   Type=simple
   User=your_username
   WorkingDirectory=/path/to/X Fin Dataset/backend
   ExecStart=/usr/bin/python3 /path/to/X Fin Dataset/backend/start_all_schedulers.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable xfin-collectors
   sudo systemctl start xfin-collectors
   ```

4. **Check Status:**
   ```bash
   sudo systemctl status xfin-collectors
   ```

5. **View Logs:**
   ```bash
   sudo journalctl -u xfin-collectors -f
   ```

---

## 🔄 Method 4: Using Task Scheduler (Windows)

### Create a Scheduled Task

1. **Open Task Scheduler:**
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task:**
   - Click "Create Basic Task"
   - Name: "X Fin Data Collectors"
   - Description: "Start all data collectors automatically"

3. **Set Trigger:**
   - Trigger: "When the computer starts"
   - OR: "When I log on"

4. **Set Action:**
   - Action: "Start a program"
   - Program/script: `C:\Python\python.exe`
   - Add arguments: `start_all_schedulers.py`
   - Start in: `C:\Users\HP\Desktop\X Fin Dataset\backend`

5. **Finish:**
   - Check "Open the Properties dialog"
   - In Properties:
     - Check "Run whether user is logged on or not"
     - Check "Run with highest privileges"
     - Under Settings: Check "Allow task to be run on demand"

---

## 🖥️ Method 5: Run Individual Schedulers (Advanced)

If you want to run schedulers separately or with custom schedules:

```bash
# Terminal 1: FII/DII Collector
python cronjob_scheduler.py

# Terminal 2: NIFTY Option Chain
python option_chain_scheduler.py

# Terminal 3: BankNifty Option Chain
python banknifty_option_chain_scheduler.py

# Terminal 4: News Collector
python news_collector_scheduler.py

# Terminal 5: HDFC Bank
python hdfcbank_option_chain_scheduler.py

# ... and so on for each bank
```

---

## 📊 Check Scheduler Status

### View Logs:
```bash
# Master scheduler log
tail -f backend/master_scheduler.log

# Individual scheduler logs
tail -f backend/cronjob_scheduler.log
tail -f backend/option_chain_scheduler.log
tail -f backend/news_collector_scheduler.log
# etc...
```

### Check Status Files:
Each scheduler creates a status JSON file:
- `backend/scheduler_status.json` (FII/DII)
- `backend/option_chain_scheduler_status.json` (NIFTY)
- `backend/banknifty_option_chain_scheduler_status.json`
- `backend/news_collector_scheduler_status.json`
- And one for each bank collector

---

## 🛑 Stop All Schedulers

### If Running Manually:
Press `Ctrl+C` in the terminal where `start_all_schedulers.py` is running.

### If Running as Service:
```cmd
# Windows (NSSM)
nssm stop XFinDataCollectors

# Linux (Systemd)
sudo systemctl stop xfin-collectors
```

---

## ✅ Verification

### Check if Schedulers are Running:

1. **Check Log Files:**
   - Logs should show regular "Collecting data..." messages
   - Latest log entries should be from recent minutes/hours

2. **Check MongoDB:**
   - Verify data is being collected in MongoDB collections
   - Check timestamps to ensure data is fresh

3. **Check Admin Panel:**
   - Open the React admin panel
   - Check status indicators - should show "Running"
   - Check "Last Run" times - should be recent

---

## 🔧 Troubleshooting

### Schedulers Not Starting:
1. Check Python path is correct
2. Verify all dependencies installed: `pip install -r requirements.txt`
3. Check MongoDB is running
4. Review log files for errors

### Data Not Collecting:
1. Check if it's market hours (09:15 AM - 03:30 PM on weekdays)
2. Verify internet connection
3. Check NSE API is accessible
4. Review individual scheduler logs

### Service Won't Start:
1. Check service logs
2. Verify file paths are correct
3. Check user permissions
4. Ensure Python executable path is correct

---

## 📝 Notes

- **Market Hours:** Option chain collectors only run during market hours (Mon-Fri, 09:15 AM - 03:30 PM IST)
- **FII/DII:** Runs once daily at 5:00 PM
- **News Collector:** Runs every 15 minutes during market hours
- **All schedulers:** Automatically skip weekends and outside market hours

---

## 🎯 Quick Start Command

**For Development (Manual):**
```bash
cd backend
python start_all_schedulers.py
```

**For Production (Windows Service):**
```cmd
nssm start XFinDataCollectors
```

**For Production (Linux):**
```bash
sudo systemctl start xfin-collectors
```

