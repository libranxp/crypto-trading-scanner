from flask import Flask, render_template
import supabase
from config import SUPABASE_URL, SUPABASE_ANON_KEY

app = Flask(__name__)

# Initialize Supabase client
from supabase import create_client
sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

@app.route("/")
def home():
    # Fetch all scanned tickers
    data = sb.table("crypto_signals").select("*").execute()
    tickers = data.data if data.data else []
    return render_template("dashboard.html", tickers=tickers)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
