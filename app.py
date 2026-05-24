import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE (FIXED ENDPOINT) ---
@st.cache_data(ttl=3600)
def fetch_congressional_trades(api_key, symbol):
    # FIXED: Switched from /api/v3/ to /stable/
    url = f"https://financialmodelingprep.com/stable/house-trades?symbol={symbol}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"HTTP {response.status_code}"}

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("Add FMP_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 3. UI & LOGIC ---
st.markdown("### 🏛️ Insider Matrix Live")
ticker = st.text_input("Enter Ticker to Scan", value="SOFI").upper()

if st.button("Scan Cluster"):
    data = fetch_congressional_trades(api_key, ticker)
    
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        
        # Display Summary
        st.success(f"Clusters Detected for {ticker}")
        
        # Display Grouped Data
        st.subheader("Recent Activity")
        st.dataframe(df[['representative', 'transactionDate', 'type', 'amount']], use_container_width=True)
    elif isinstance(data, dict) and "error" in data:
        st.error(f"API Error: {data['error']}")
    else:
        st.warning("No data found for this ticker.")