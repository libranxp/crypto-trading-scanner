from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

results = supabase.table("alerts").select("*").order("created_at", desc=True).limit(20).execute()

for coin in results.data:
    st.subheader(f"{coin['symbol'].upper()}")
    st.write(f"AI Score: {coin['ai_score']}")
    st.write(f"Sentiment: {coin['sentiment_score']}")
    st.write(f"Catalysts: {coin['catalysts']}")
    st.markdown("---")
