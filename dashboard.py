import streamlit as st
import requests
import pandas as pd

# URL of your deployed FastAPI backend
API_BASE_URL = "https://crypto-trading-scanner.onrender.com"

st.set_page_config(page_title="Crypto Trading Scanner Dashboard", layout="wide")

st.title("🚀 Crypto Trading Scanner Live Dashboard")

# Fetch Tier 1 data
@st.cache(ttl=300)
def fetch_tier1_data():
    try:
        resp = requests.get(f"{API_BASE_URL}/scan/auto")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch Tier 1 data: {e}")
        return None

# Fetch Tier 2 data for selected symbols
def fetch_tier2_data(symbols):
    try:
        params = {"symbols": ",".join(symbols)}
        resp = requests.get(f"{API_BASE_URL}/scan/manual", params=params)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch Tier 2 data: {e}")
        return None

tier1_data = fetch_tier1_data()

if tier1_data and "results" in tier1_data:
    df = pd.DataFrame(tier1_data["results"])

    # Show basic market data table
    st.subheader("Tier 1: Market Data")
    st.dataframe(df[["symbol", "name", "price", "market_cap", "volume", "lunarcrush_sentiment"]])

    # Show news if available
    if "news" in tier1_data and tier1_data["news"]:
        st.subheader("Trending Crypto News")
        for article in tier1_data["news"]:
            st.markdown(f"- [{article['title']}]({article['url']})")

    # Select symbols for Tier 2 scan
    st.subheader("Tier 2: Manual Scan & Alerts")
    symbols = st.multiselect("Select symbols to scan (Tier 2)", options=df["symbol"].tolist())

    if st.button("Run Tier 2 Scan"):
        if symbols:
            tier2_data = fetch_tier2_data(symbols)
            if tier2_data and "results" in tier2_data:
                tier2_df = pd.DataFrame(tier2_data["results"])
                if not tier2_df.empty:
                    st.success(f"Found {len(tier2_df)} coins matching Tier 2 criteria")
                    st.dataframe(tier2_df)
                else:
                    st.info("No coins matched Tier 2 criteria.")
            else:
                st.error("Failed to get Tier 2 scan results.")
        else:
            st.warning("Please select at least one symbol.")

else:
    st.error("No Tier 1 data available.")
