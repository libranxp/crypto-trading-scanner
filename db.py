# db.py
import os
import logging
from typing import Optional

try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
TABLE = os.getenv("SUPABASE_TABLE", "signals")  # default table name

supabase: Optional[Client] = None

if SUPABASE_URL and (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY) and create_client:
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    try:
        supabase = create_client(SUPABASE_URL, key)
    except Exception as e:
        logging.exception("Failed to create supabase client: %s", e)
        supabase = None
else:
    logging.warning(
        "Supabase not configured (SUPABASE_URL or keys missing). App will run but DB features disabled."
    )

def insert_signal(payload: dict):
    """Insert a single row into supabase table (if configured)."""
    if not supabase:
        logging.debug("Supabase not available; skipping insert.")
        return None
    try:
        return supabase.table(TABLE).insert(payload).execute()
    except Exception as e:
        logging.exception("Supabase insert failed: %s", e)
        return None

def upsert_signal(payload: dict, on_conflict="ticker"):
    if not supabase:
        return None
    try:
        return supabase.table(TABLE).upsert(payload, on_conflict=on_conflict).execute()
    except Exception as e:
        logging.exception("Supabase upsert failed: %s", e)
        return None
