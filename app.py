import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA FETCHING ---
@st.cache_data(ttl=3600)
def fetch_congressional_trades(api_key):
    # Testing with AAPL to ensure we get data back
    url = f"https://financialmodelingprep.com/api/v3/congress-trading?symbol=AAPL&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json() # Returns a list
        else:
            return {"error": f"HTTP {response.status_code}", "text": response.text}
    except Exception as e:
        return {"error": str(e)}

# --- 2. CONFIGURATION ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("FMP_API_KEY not found in Streamlit Secrets.")
    st.stop()

# --- 3. UI ---
st.markdown("### 🏛️ Insider Matrix Live")
data = fetch_congressional_trades(api_key)

# Tab structure for Analysis and Debugging
tab1, tab2 = st.tabs(["🏛️ Insider Matrix", "🛠️ Debug Raw Data"])

with tab2:
    st.write("Raw API Response (If empty, your API Key/Endpoint is the issue):")
    st.json(data)

with tab1:
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found for AAPL. Ensure your FMP account has 'Congressional Trading' enabled.")