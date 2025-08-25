import os
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

TABLE = "scanner_results"

if not SUPABASE_URL or not (SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY):
    raise RuntimeError("❌ Supabase env vars missing. Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/ANON_KEY in Render.")

# Prefer service role for writes, fallback to anon
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
