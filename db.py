from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase env vars missing: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/ANON_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
TABLE = SUPABASE_TABLE
