# NSE FII/DII Data Collector

Automated cronjob to collect FII/DII trade data from NSE India API and store it in MongoDB.

## Features

- ✅ Scheduled collection (Monday to Friday at 5:00 PM)
- ✅ Retry mechanism (3 attempts with 5-second delay)
- ✅ Duplicate prevention (unique constraint on date + category)
- ✅ Comprehensive error handling and logging
- ✅ MongoDB integration with automatic reconnection

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Configure MongoDB settings:
   - Copy `.env.example` to `.env`
   - Update MongoDB connection settings in `.env`

## Configuration

Edit `.env` file:

```env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB_NAME=nse_data
MONGO_COLLECTION_NAME=fiidii_trades
```

For MongoDB with authentication:
```env
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password
```

## Usage

### Run as Cronjob (Scheduled)

Start the scheduler:
```bash
python cronjob_scheduler.py
```

This will:
- Run automatically every Monday to Friday at 5:00 PM (17:00)
- Continue running in the background

### Run Manually (One-time)

Execute the collector manually:
```bash
python nse_fiidii_collector.py
```

## Data Structure

The script stores data in MongoDB with the following structure:

```json
{
    "category": "DII **",
    "date": "31-Oct-2025",
    "buyValue": "18633.9",
    "sellValue": "11565.46",
    "netValue": "7068.44",
    "insertedAt": ISODate("..."),
    "updatedAt": ISODate("...")
}
```

## Duplicate Prevention

- Unique index on `date` + `category` combination
- If a record with the same date and category exists, it will be updated
- New records are inserted automatically

## Error Handling

- **Retry Logic**: 3 attempts with 5-second delay between retries
- **Error Logging**: All errors logged to `nse_collector.log` and `cronjob_scheduler.log`
- **Exception Handling**: Comprehensive try-catch blocks throughout

## Logs

- `nse_collector.log` - Data collection logs
- `cronjob_scheduler.log` - Scheduler execution logs

## System Requirements

- Python 3.7+
- MongoDB 3.6+
- Internet connection for API access

