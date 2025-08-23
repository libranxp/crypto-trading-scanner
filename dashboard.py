# dashboard.py

import streamlit as st
import requests

st.title("Crypto Trading Scanner Dashboard")

API_URL = "https://crypto-trading-scanner.onrender.com/scan/auto"

st.write("Fetching live data...")
try:
    resp = requests.get(API_URL, timeout=60)
    data = resp.json()
    results = data.get("results", [])
    if not results:
        st.warning("No coins passed the scanner filters at this time.")
    else:
        for coin in results:
            st.subheader(f"{coin['name']} ({coin['symbol']})")
            st.write(f"Price: ${coin['price']}")
            st.write(f"Market Cap: ${coin['market_cap']:,}")
            st.write(f"Volume: ${coin['volume']:,}")
            st.write(f"24h Change: {coin['price_change_24h']}%")
            st.write(f"RSI: {coin['rsi']:.2f}")
            st.write(f"RVOL: {coin['rvol']:.2f}")
            st.write(f"Sentiment: {coin['sentiment_score']:.2f}")
            st.write(f"[View on CoinGecko]({coin['coingecko_url']})")
            st.markdown("---")
except Exception as e:
    st.error(f"Error fetching data: {e}")
