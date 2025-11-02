# Admin Panel - NSE FII/DII Data Collector

## Overview

The admin panel provides a web-based interface to monitor and manage the NSE FII/DII data collection system.

## Features

- ✅ **Cronjob Status**: Real-time monitoring of scheduler status (Running/Stopped)
- ✅ **Next Run Time**: Shows when the next scheduled collection will occur
- ✅ **Last Run Info**: Displays last execution time and status
- ✅ **Statistics**: Total records count and latest date
- ✅ **Data View**: Complete table view of all collected data
- ✅ **Manual Trigger**: Button to manually trigger data collection
- ✅ **Auto-refresh**: Updates every 30 seconds automatically

## Installation

1. Install dependencies (if not already done):
```bash
cd backend
pip install -r requirements.txt
```

## Usage

### Start the Admin Panel

```bash
cd backend
python admin_panel.py
```

The admin panel will start on: **http://localhost:5000**

### Start the Cronjob Scheduler (Separate Process)

In a separate terminal window:

```bash
cd backend
python cronjob_scheduler.py
```

## Admin Panel Features

### Status Dashboard
- **Status Badge**: Green (Running) or Red (Stopped)
- **Next Run**: Calculated based on schedule (Mon-Fri at 5:00 PM)
- **Last Run**: When the last collection was executed
- **Last Status**: Success/Failed/Error

### Statistics
- **Total Records**: Count of all records in MongoDB
- **Latest Date**: Most recent date in the database

### Data Table
- Displays all collected records
- Shows DII and FII data side by side
- Color-coded net values (green for positive, red for negative)
- Sortable by date (newest first)

### Manual Actions
- **Refresh Status**: Manually refresh all information
- **Trigger Collection Now**: Immediately run data collection

## API Endpoints

The admin panel exposes these REST API endpoints:

- `GET /api/status` - Get scheduler status
- `GET /api/data` - Get all collected data
- `GET /api/stats` - Get statistics
- `POST /api/trigger` - Manually trigger collection

## Notes

- The admin panel checks if the scheduler process is running by looking for `cronjob_scheduler.py` in running processes
- Status information is saved to `scheduler_status.json` by the scheduler
- Data auto-refreshes every 30 seconds
- Make sure MongoDB is running before starting the admin panel

