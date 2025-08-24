import streamlit as st
import requests
import time

st.set_page_config(page_title="Crypto Scanner", layout="wide")
st.title("⚡ Crypto Trading Scanner")

API_BASE = st.secrets.get("API_URL", "https://crypto-trading-scanner.onrender.com")

tab1, tab2 = st.tabs(["Tier 1 (Auto)", "Tier 2 (Manual)"])

with tab1:
    st.caption("Lightweight filters. Auto every 45 min (08:00–21:00 BST). Also runnable on demand.")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Run Tier 1 Now", use_container_width=True):
            with st.spinner("Running Tier 1…"):
                r = requests.get(f"{API_BASE}/scan/auto", timeout=90)
                t1 = r.json()
        else:
            r = requests.get(f"{API_BASE}/results/tier1", timeout=60)
            t1 = r.json()

    results = t1.get("results", [])
    if not results:
        st.warning("No Tier 1 matches yet.")
    else:
        st.success(f"{len(results)} symbols passed Tier 1")
        for coin in results:
            with st.expander(f"{coin['name']} ({coin['symbol']})  •  ${coin['price']:.4f}"):
                st.write(f"Market Cap: ${coin['market_cap']:,}  |  Volume(24h): ${coin['volume']:,}")
                st.write(f"24h Change: {coin['price_change_24h']:.2f}%")
                st.write(f"RSI: {coin['rsi']:.2f}  •  RVOL: {coin['rvol']:.2f}  •  EMA aligned: {coin['ema_aligned']}  •  VWAP Δ: {coin['vwap_proximity']*100:.2f}%")
                st.markdown(f"[View on CoinGecko]({coin['coingecko_url']})")

with tab2:
    st.caption("Deep technical + sentiment + catalysts. Sends Telegram alerts. Trigger manually.")
    if st.button("Run Tier 2 Now", type="primary", use_container_width=True):
        with st.spinner("Running Tier 2…"):
            r = requests.post(f"{API_BASE}/scan/tier2", timeout=120)
            t2 = r.json()
    else:
        r = requests.get(f"{API_BASE}/results/tier2", timeout=60)
        t2 = r.json()

    results2 = t2.get("results", [])
    if not results2:
        st.info("No Tier 2 results yet.")
    else:
        for coin in results2:
            with st.expander(f"🔔 {coin['name']} ({coin['symbol']})  •  AI {coin.get('ai_score','?')}  •  Risk {coin.get('risk','?')}"):
                st.write(f"Price: ${coin['price']:.4f} | MC: ${coin['market_cap']:,} | Vol: ${coin['volume']:,}")
                st.write(f"RSI: {coin['rsi']:.2f} • RVOL: {coin['rvol']:.2f} • VWAP Δ: {coin['vwap_proximity']*100:.2f}%")
                st.write(f"Sentiment: {coin.get('sentiment_score',0):.2f} | Mentions: {coin.get('mentions',0)} | Engagement: {coin.get('engagement',0)} | Events: {coin.get('events',0)}")
                st.markdown(f"[CoinGecko]({coin.get('coingecko_url','')})")
