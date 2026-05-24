import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_congressional_trades(api_key, symbol):
    url = f"https://financialmodelingprep.com/stable/house-trades?symbol={symbol}&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 402:
            return {"error": "Payment Required (Premium Data)"}
        else:
            return {"error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")

# --- 3. UI ---
st.markdown("### 🏛️ Insider Matrix Live")
ticker = st.text_input("Enter Ticker to Scan", value="SOFI").upper()

if st.button("Scan Cluster"):
    if not api_key:
        st.error("Add FMP_API_KEY to Streamlit Secrets.")
    else:
        data = fetch_congressional_trades(api_key, ticker)
        
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            st.success(f"Trade data found for {ticker}")
            st.dataframe(df, use_container_width=True)
        elif isinstance(data, dict) and "error" in data:
            st.warning(f"Note: {data['error']}. This endpoint requires a paid FMP subscription.")
            st.info("Tip: You can use the 'History Tab' below to log trades manually.")
        else:
            st.warning("No data found for this ticker.")

# --- 4. HISTORY TAB (Manual Fallback) ---
if 'manual_trades' not in st.session_state:
    st.session_state.manual_trades = pd.DataFrame(columns=["ticker", "member", "date", "result"])

with st.expander("📊 Manual History / Cluster Tracker (Edit here)"):
    st.session_state.manual_trades = st.data_editor(st.session_state.manual_trades, num_rows="dynamic", use_container_width=True)
