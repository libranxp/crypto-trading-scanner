# db.py
import os
from supabase import create_client, Client

# Grab Supabase credentials from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Make sure at least one key is present
if not SUPABASE_URL or not (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY):
    raise RuntimeError("Supabase env vars missing: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/ANON_KEY")

# Use service role key if available, else anon key
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY)

# Example table name (replace with your actual table)
TABLE = "crypto_scan_data"
