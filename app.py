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
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_ticker_trades(api_key, ticker):
    # CORRECTED: Using the /stable/ endpoint
    url = f"https://financialmodelingprep.com/stable/house-trades?symbol={ticker}&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("Add FMP_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 3. SCANNER LOGIC ---
st.markdown("### 🏛️ Insider Matrix Live")
tickers_to_scan = ["SOFI", "PLTR", "AAPL", "TSLA", "NVDA"]
all_trades = []

# Fetch trades for each ticker
for ticker in tickers_to_scan:
    data = fetch_ticker_trades(api_key, ticker)
    if data:
        all_trades.extend(data)

df = pd.DataFrame(all_trades)

if not df.empty:
    # Cluster Detection: Group by symbol and count unique representatives
    clusters = df.groupby('symbol').agg(
        size=('representative', 'nunique'),
        members=('representative', lambda x: ', '.join(x.unique()))
    ).reset_index()

    # Display Matrix
    for _, item in clusters.iterrows():
        with st.container(border=True):
            st.markdown(f"### {item['symbol']} | Cluster Size: {item['size']}")
            st.markdown(f"**Members:** {item['members']}")
else:
    st.warning("No recent trades found for these tickers.")