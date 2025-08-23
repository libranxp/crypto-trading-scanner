from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_alert_to_db(alert):
    supabase.table("alerts").insert(alert).execute()
