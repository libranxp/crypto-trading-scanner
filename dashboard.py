import streamlit as st
import requests

st.title("📊 Crypto Trading Scanner Dashboard")

API_BASE = "https://crypto-trading-scanner.onrender.com"

# Toggle between scans
scan_type = st.selectbox("Choose Scan Type", ["Auto (Tier 1)", "Manual (Tier 2)"])

if scan_type == "Auto (Tier 1)":
    endpoint = "/scan/auto"
else:
    endpoint = "/scan/manual"

try:
    resp = requests.get(API_BASE + endpoint, timeout=60)
    data = resp.json()
    results = data.get("results", [])

    if not results:
        st.warning("No coins passed the scanner filters at this time.")
    else:
        for coin in results:
            st.subheader(f"{coin['name']} ({coin['symbol']})")
            if "price" in coin:
                st.write(f"💰 Price: ${coin['price']}")
                st.write(f"📊 Market Cap: ${coin['market_cap']:,}")
                st.write(f"📈 Volume: ${coin['volume']:,}")
                st.write(f"📉 24h Change: {coin['price_change_24h']}%")
                st.write(f"📊 RSI: {coin['rsi']}")
                st.write(f"📊 RVOL: {coin['rvol']}")
                st.write(f"[View on CoinGecko]({coin['coingecko_url']})")
            else:
                st.write(f"🤖 AI Score: {coin.get('ai_score')}")
                st.write(f"⚠️ Risk: {coin.get('risk')}")
                st.write(f"⭐ Sentiment Score: {coin.get('sentiment_score')}")
            st.markdown("---")

except Exception as e:
    st.error(f"Error fetching data: {e}")
