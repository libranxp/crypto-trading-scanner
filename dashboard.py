import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

# FastAPI app
app = FastAPI(title="Crypto Dashboard", version="1.0")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
async def root():
    return {"message": "🚀 Crypto Scanner Dashboard is running"}

@app.get("/dashboard")
async def get_dashboard():
    """Fetch latest Tier1 scan results from Supabase."""
    try:
        response = supabase.table("scanner_results").select("*").order("id", desc=True).limit(50).execute()
        return {"status": "success", "results": response.data}
    except Exception as e:
        logging.error(f"❌ Dashboard fetch failed: {e}")
        return {"status": "error", "message": str(e)}
