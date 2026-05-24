import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA FETCHING (FREE ENDPOINT) ---
@st.cache_data(ttl=3600)
def fetch_insider_trades(api_key):
    # This is the FREE endpoint (latest insider trades)
    url = f"https://financialmodelingprep.com/api/v3/insider-trading?page=0&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("Add FMP_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 3. LOGIC ---
st.markdown("### 🏛️ Insider Matrix Live (Free Tier)")
min_cluster = st.slider("Minimum Insiders in Cluster", 1, 5, 2)

df = fetch_insider_trades(api_key)

if not df.empty:
    # Cluster detection: group by ticker and count unique insider names
    clusters = df.groupby('symbol').agg(
        size=('reportingName', 'nunique'),
        members=('reportingName', lambda x: ', '.join(x.unique())),
        last_transaction=('transactionDate', 'max')
    ).reset_index()

    active_clusters = clusters[clusters['size'] >= min_cluster]

    # --- UI ---
    if not active_clusters.empty:
        for _, item in active_clusters.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"### {item['symbol']} | Cluster Size: {item['size']}")
                col2.write(f"Latest: {item['last_transaction']}")
                st.markdown(f"**Insiders:** {item['members']}")
    else:
        st.warning("No clusters found in the latest 100 trades. Try lowering the slider.")
else:
    st.error("Could not fetch data. Check your API key and ensure it is active.")

# --- 4. HISTORY ---
with st.expander("📊 View All Raw Insider Trades"):
    st.dataframe(df, use_container_width=True)