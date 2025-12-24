"""
Sensex Option Chain Scheduler (BSE)

Polls the latest Sensex option-chain data from BSE every 3 minutes
between 09:15 and 15:30 local time and upserts the full payload into MongoDB.

DB:   nse_data
Coll: sensex_option_chain_data

De-dupe key: payload timestamp at ASON.DT_TM (trimmed).

Environment:
  - MONGO_URI (optional): Mongo connection string. Defaults to mongodb://localhost:27017
"""

from __future__ import annotations

import datetime as dt
import json
import os
import time
from typing import Any, Dict

import requests
from pymongo import MongoClient
from pymongo.collection import Collection

# Market window (assumed local time)
MARKET_START = dt.time(hour=9, minute=15)
MARKET_END = dt.time(hour=15, minute=30)

# Endpoints and headers
EXPIRY_URL = "https://api.bseindia.com/BseIndiaAPI/api/ddlExpiry_IV/w?ProductType=IO&scrip_cd=1"
CHAIN_URL_TEMPLATE = (
    "https://api.bseindia.com/BseIndiaAPI/api/DerivOptionChain_IV/w?Expiry={expiry}&scrip_cd=1&strprice=0"
)
COMMON_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.bseindia.com",
    "Referer": "https://www.bseindia.com/",
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
    ),
}

STATUS_FILE = "sensex_option_chain_scheduler_status.json"


def is_market_time(now: dt.datetime | None = None) -> bool:
    """Return True if the current local time is within the market window."""
    now = now or dt.datetime.now()
    return MARKET_START <= now.time() <= MARKET_END


def get_mongo_collection() -> Collection:
    """Return the Mongo collection handle for Sensex option-chain data."""
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    return client["nse_data"]["sensex_option_chain_data"]


def fetch_first_expiry() -> str:
    """Fetch the nearest expiry from BSE and return it URL encoded."""
    resp = requests.get(EXPIRY_URL, headers=COMMON_HEADERS, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    table1 = payload.get("Table1") or []
    if not table1:
        raise ValueError("No expiries returned from expiry API")
    expiry_raw = table1[0].get("ExpiryDate")
    if not expiry_raw:
        raise ValueError("First expiry is missing ExpiryDate")
    # API expects spaces as + in the query string
    return expiry_raw.replace(" ", "+")


def fetch_option_chain(expiry: str) -> Dict[str, Any]:
    """Fetch the option-chain payload for the provided expiry."""
    url = CHAIN_URL_TEMPLATE.format(expiry=expiry)
    resp = requests.get(url, headers=COMMON_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def upsert_chain(coll: Collection, data: Dict[str, Any]) -> str:
    """
    Insert the option-chain payload using insert time as unique identifier.
    Always inserts a new record with insertedAt timestamp to ensure uniqueness.
    Sets default values for records.timestamp and records.expiry when null to avoid unique index conflicts.
    Returns the DT_TM timestamp.
    """
    # Get ASON.DT_TM for logging
    dt_tm = (data.get("ASON") or {}).get("DT_TM", "")
    dt_tm = dt_tm.strip() if isinstance(dt_tm, str) else ""
    
    if not dt_tm:
        raise ValueError("Missing ASON.DT_TM in option-chain payload")
    
    # Create a deep copy of data to modify
    import copy
    data_to_insert = copy.deepcopy(data)
    
    # Get records.timestamp and records.expiry
    records = data_to_insert.get("records", {})
    if not isinstance(records, dict):
        records = {}
        data_to_insert["records"] = records
    
    timestamp = records.get("timestamp")
    expiry = records.get("expiry")
    
    # If timestamp or expiry are null, set them to unique values based on insert time
    # This prevents duplicate key errors on the unique index
    inserted_at = dt.datetime.utcnow()
    inserted_at_str = inserted_at.isoformat()
    
    if timestamp is None:
        # Use insert time as timestamp to make it unique
        records["timestamp"] = inserted_at_str
        print(f"[{dt.datetime.now()}] Setting null timestamp to insert time: {inserted_at_str}")
    
    if expiry is None:
        # Use insert time + small offset as expiry to make it unique
        # Add microseconds to ensure uniqueness
        expiry_str = f"{inserted_at_str}_expiry"
        records["expiry"] = expiry_str
        print(f"[{dt.datetime.now()}] Setting null expiry to unique value: {expiry_str}")
    
    # Add insertedAt timestamp to track when record was inserted
    data_to_insert["insertedAt"] = inserted_at
    data_to_insert["insertedAtLocal"] = dt.datetime.now().isoformat()
    
    # Always insert a new record
    try:
        result = coll.insert_one(data_to_insert)
        
        # Verify the record was actually inserted
        if result.inserted_id:
            inserted_record = coll.find_one({"_id": result.inserted_id})
            if inserted_record:
                print(f"[{dt.datetime.now()}] ✅ Successfully inserted new record: ASON.DT_TM={dt_tm}, _id={result.inserted_id}, insertedAt={inserted_at}")
                return dt_tm
            else:
                print(f"[{dt.datetime.now()}] ⚠️ Warning: Insert reported success but record not found: ASON.DT_TM={dt_tm}, _id={result.inserted_id}")
                return dt_tm
        else:
            print(f"[{dt.datetime.now()}] ❌ Error: Insert failed - no inserted_id returned: ASON.DT_TM={dt_tm}")
            raise ValueError("Insert failed - no inserted_id returned")
    except Exception as e:
        # If duplicate key error still occurs, log it but don't crash
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            print(f"[{dt.datetime.now()}] ❌ Duplicate key error (should not happen with unique timestamps): ASON.DT_TM={dt_tm}, error={e}")
            # Return dt_tm to avoid breaking the scheduler
            return dt_tm
        else:
            # Re-raise if it's not a duplicate key error
            print(f"[{dt.datetime.now()}] ❌ Unexpected error: {e}")
            raise


def update_status(last_status: str, error: str | None = None, dt_tm: str | None = None) -> None:
    """Persist the latest run status to a small JSON file for visibility."""
    status = {
        "last_run": dt.datetime.now().isoformat(),
        "last_status": last_status,
    }
    if dt_tm:
        status["last_dt_tm"] = dt_tm
    if error:
        status["error"] = error
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except Exception:
        # Status updates shouldn't crash the scheduler
        pass


def run_once(coll: Collection) -> None:
    """Run a single poll + upsert cycle."""
    expiry = fetch_first_expiry()
    chain = fetch_option_chain(expiry)
    
    # Log collection stats before insert
    total_before = coll.count_documents({})
    print(f"[{dt.datetime.now()}] Collection stats before insert: total records={total_before}")
    
    dt_tm = upsert_chain(coll, chain)
    
    # Log collection stats after insert
    total_after = coll.count_documents({})
    print(f"[{dt.datetime.now()}] Collection stats after insert: total records={total_after} (change: {total_after - total_before})")
    
    # Verify the record exists
    saved_record = coll.find_one({"ASON.DT_TM": dt_tm})
    if saved_record:
        print(f"[{dt.datetime.now()}] ✅ Verified record exists in DB: ASON.DT_TM={dt_tm}, _id={saved_record.get('_id')}")
    else:
        print(f"[{dt.datetime.now()}] ❌ ERROR: Record not found in DB after insert: ASON.DT_TM={dt_tm}")
    
    print(f"[{dt.datetime.now()}] Stored option chain for expiry={expiry} DT_TM={dt_tm}")
    update_status("success", dt_tm=dt_tm)


def main() -> None:
    """Run the scheduler loop."""
    coll = get_mongo_collection()
    while True:
        if is_market_time():
            try:
                run_once(coll)
            except Exception as exc:  # noqa: BLE001
                print(f"[{dt.datetime.now()}] Error: {exc}")
                update_status("error", error=str(exc))
            time.sleep(180)  # 3 minutes
        else:
            # Outside market hours, poll every minute until window opens
            time.sleep(60)


if __name__ == "__main__":
    main()

