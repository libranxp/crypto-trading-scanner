import streamlit as st
import pandas as pd
import requests

# Replace with your deployed backend URL (crypto-trading-scanner service)
API_BASE_URL = "https://YOUR-BACKEND-URL.onrender.com"

st.set_page_config(page_title="Crypto Scanner Dashboard", layout="wide")
st.title("🪙 Crypto Scanner Dashboard")

@st.cache_data(ttl=300)
def fetch_data():
    try:
        resp = requests.get(f"{API_BASE_URL}/scan/auto", timeout=120)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return {"results": []}

data = fetch_data()
results = data.get("results", [])

if results:
    df = pd.DataFrame(results)
    # Optional: Format columns for readability
    if "price" in df.columns:
        df["price"] = df["price"].map(lambda x: f"${x:,.4f}")
    if "market_cap" in df.columns:
        df["market_cap"] = df["market_cap"].map(lambda x: f"${x:,.0f}")
    if "volume" in df.columns:
        df["volume"] = df["volume"].map(lambda x: f"${x:,.0f}")
    if "price_change_24h" in df.columns:
        df["price_change_24h"] = df["price_change_24h"].map(lambda x: f"{x:.2f}%")
    if "sentiment_score" in df.columns:
        df["sentiment_score"] = df["sentiment_score"].map(lambda x: f"{x:.2f}")

    # Show a summary
    st.success(f"Found {len(df)} coins matching all scanner criteria.")

    # Show the table
    st.dataframe(df, use_container_width=True)

    # Optionally, allow user to click for more info
    st.markdown("### Coin Details")
    selected = st.selectbox("Select a coin for more details", df["symbol"])
    coin_row = df[df["symbol"] == selected].iloc[0]
    st.json(coin_row.to_dict())

    # Optionally, show links
    if "coinmarketcap_url" in coin_row:
        st.markdown(f"[View on CoinMarketCap]({coin_row['coinmarketcap_url']})")
else:
    st.warning("No coins currently match all scanner criteria.")

st.caption("Data updates every 5 minutes. Powered by your multi-API crypto scanner.")
