# /services/scanner.py
from db import supabase, TABLE
import logging

logging.basicConfig(level=logging.INFO)

def run_auto_scan():
    try:
        # Example: fetch all rows from your table
        data = supabase.table(TABLE).select("*").execute()
        logging.info(f"Fetched {len(data.data)} rows")
        return data.data
    except Exception as e:
        logging.error(f"Failed to run scan: {e}")
        return []
