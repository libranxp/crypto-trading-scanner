import streamlit as st
import requests
import os

API_BASE = os.environ.get("SCANNER_API_URL", "https://crypto-trading-scanner.onrender.com")

st.set_page_config(page_title="Crypto Scanner Dashboard", layout="wide")
st.title("Crypto Trading Scanner Dashboard")

tab1, tab2 = st.tabs(["Tier 1 — Auto Scan", "Tier 2 — Manual Scan"])

with tab1:
    st.header("Tier 1 — Lightweight Auto Scan")
    if st.button("Refresh Tier 1 now"):
        st.experimental_rerun()

    try:
        resp = requests.get(f"{API_BASE}/scan/auto", timeout=60)
        data = resp.json()
        results = data.get("results", [])
        if not results:
            st.info("No coins passed the scanner filters at this time.")
        else:
            for coin in results:
                with st.expander(f"{coin.get('name','')} ({coin.get('symbol','')})", expanded=False):
                    cols = st.columns(3)
                    cols[0].write(f"**Price:** ${coin.get('price',0):.6f}")
                    cols[0].write(f"**Market Cap:** ${int(coin.get('market_cap',0)):,}")
                    cols[0].write(f"**Volume (24h):** ${int(coin.get('volume',0)):,}")
                    cols[1].write(f"**24h Change:** {coin.get('price_change_24h',0):.2f}%")
                    cols[1].write(f"**RSI:** {coin.get('rsi', 0):.2f}")
                    cols[1].write(f"**RVOL:** {coin.get('rvol', 0):.2f}")
                    cols[2].write(f"**EMA aligned:** {coin.get('ema_aligned')}")
                    cols[2].write(f"**VWAP prox:** {coin.get('vwap_proximity',0)*100:.2f}%")
                    cols[2].write(f"[View on CoinGecko]({coin.get('coingecko_url','')})")
    except Exception as e:
        st.error(f"Error fetching Tier1: {e}")

with tab2:
    st.header("Tier 2 — Manual Scan")
    symbols_input = st.text_input("Symbols (comma separated): e.g. BTC,ETH,SOL")
    if st.button("Run Tier 2 check"):
        query = symbols_input.strip()
        if query:
            try:
                resp = requests.get(f"{API_BASE}/scan/manual", params={"symbols": query}, timeout=60)
                data = resp.json()
                results = data.get("results", [])
                if not results:
                    st.info("No results.")
                else:
                    for r in results:
                        if r.get("error"):
                            st.warning(f"{r.get('symbol')}: {r.get('error')}")
                            continue
                        st.subheader(f"{r.get('name')} ({r.get('symbol')})")
                        st.write(f"AI Score: {r.get('ai_score')}  —  Risk: {r.get('risk')}")
                        st.write(f"RSI: {r.get('rsi'):.2f}  RVOL: {r.get('rvol'):.2f}  EMA aligned: {r.get('ema_aligned')}")
                        st.write(f"Sentiment: {r.get('sentiment_score')}")
                        st.markdown("---")
            except Exception as e:
                st.error(f"Tier2 request failed: {e}")
        else:
            st.info("Please enter symbols to run Tier 2 check.")
