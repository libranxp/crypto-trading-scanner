# db.py
import os
import logging
from supabase import create_client, Client
from typing import Optional

logger = logging.getLogger(__name__)

# Table name used by the dashboard
TABLE = "scanner_results"

def _get_env_var(*names) -> Optional[str]:
    """Return the first non-empty env var from names."""
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return None

def get_supabase() -> Client:
    """
    Create and return a Supabase client.
    Uses SUPABASE_URL + (SUPABASE_SERVICE_ROLE_KEY OR SUPABASE_ANON_KEY).
    Raises RuntimeError with a helpful message if missing.
    """
    url = _get_env_var("SUPABASE_URL")
    key = _get_env_var("SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY", "SUPABASE_ANONKEY")

    if not url or not key:
        msg = (
            "Supabase env vars missing. Ensure SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY are set."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    try:
        supabase = create_client(url, key)
        # quick test: attempt to fetch 0 rows (safe read)
        supabase.table(TABLE).select("symbol").limit(0).execute()
        return supabase
    except Exception as e:
        logger.exception("Failed to create Supabase client or test table access: %s", e)
        raise
