import streamlit as st
from scanner_tier1 import tier1_scan
from scanner_tier2 import tier2_scan

st.title("🚀 Crypto Trading Scanner Dashboard")

try:
    tier1_symbols = tier1_scan()  # lightweight filter
    if not tier1_symbols:
        st.warning("No coins passed Tier1 filters at this time.")
    else:
        alerts = tier2_scan(tier1_symbols)  # deep scan
        if not alerts:
            st.info("No coins passed Tier2 criteria.")
        else:
            for coin in alerts:
                st.subheader(f"{coin['symbol'].upper()}")
                st.write(f"AI Score: {coin['ai_score']:.2f}")
                st.write(f"Catalysts: {coin['catalysts']}")
                st.write(f"Twitter Mentions: {coin['twitter']['mentions']}")
                st.markdown("---")
except Exception as e:
    st.error(f"Error fetching data: {e}")
