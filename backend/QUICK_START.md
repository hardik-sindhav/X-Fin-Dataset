# 🚀 Quick Start - Run All Cronjobs Automatically

## ✅ Simplest Method (Recommended)

### Windows:
```cmd
cd backend
start_schedulers.bat
```

### Linux/Mac:
```bash
cd backend
chmod +x start_schedulers.sh
./start_schedulers.sh
```

### Or Directly with Python:
```bash
cd backend
python start_all_schedulers.py
```

---

## 📋 What Gets Started?

The master scheduler starts **16 data collectors** automatically:

1. **FII/DII** - Mon-Fri @ 5:00 PM (once daily)
2. **NIFTY Option Chain** - Mon-Fri 09:15 AM - 03:30 PM (every 3 min)
3. **BankNifty Option Chain** - Mon-Fri 09:15 AM - 03:30 PM (every 3 min)
4. **News Collector** - Mon-Fri 09:00 AM - 03:30 PM (every 15 min)
5. **12 Bank Options** - Each runs Mon-Fri 09:15 AM - 03:30 PM (every 3 min)
   - HDFC Bank, ICICI Bank, SBIN, Kotak Bank, Axis Bank
   - Bank of Baroda, PNB, CANBK, AUBANK, IndusInd Bank
   - IDFC First Bank, Federal Bank

---

## 🔧 Setup for Auto-Start on Boot

### Windows: Use Task Scheduler
1. Press `Win + R`, type `taskschd.msc`
2. Create Basic Task → "Start a program"
3. Program: `python.exe`
4. Arguments: `start_all_schedulers.py`
5. Start in: `C:\Users\HP\Desktop\X Fin Dataset\backend`
6. Trigger: "When computer starts"

### Linux/Mac: Use Systemd
See `START_SCHEDULERS.md` for detailed instructions.

---

## 📊 Check Status

**View Logs:**
```bash
# Master log
tail -f backend/master_scheduler.log

# Individual logs
tail -f backend/cronjob_scheduler.log
tail -f backend/option_chain_scheduler.log
```

**Check Admin Panel:**
- Open React admin panel at http://localhost:3000
- Check status indicators - should show "Running"
- Verify "Last Run" times are recent

---

## 🛑 Stop All Schedulers

Press `Ctrl+C` in the terminal where schedulers are running.

---

**For detailed setup instructions, see: `START_SCHEDULERS.md`**

