import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_live_trades(api_key):
    # FMP House Trades Endpoint
    url = f"https://financialmodelingprep.com/api/v3/congress-trading?page=0&apikey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        # Rename columns to standard names for processing
        return df.rename(columns={"symbol": "ticker", "representative": "member"})
    return pd.DataFrame()

# --- 2. LOGIC ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("Please set FMP_API_KEY in Streamlit Secrets.")
    st.stop()

df = fetch_live_trades(api_key)

if not df.empty:
    # Grouping logic to detect clusters
    clusters = df.groupby('ticker').agg(
        size=('member', 'nunique'),
        members=('member', lambda x: ', '.join(x.unique())),
        last_trade=('transactionDate', 'max')
    ).reset_index()

    # --- 3. UI: LIVE SCANNER ---
    st.markdown("### 🏛️ Insider Matrix Live")
    min_cluster = st.slider("Minimum Executives in Cluster", 1, 5, 2)
    active_clusters = clusters[clusters['size'] >= min_cluster]

    for _, item in active_clusters.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.markdown(f"### {item['ticker']}")
            col2.metric("Cluster Size", f"{item['size']} Officials")
            col3.write(f"Last Trade: {item['last_trade']}")
            st.markdown(f"**Members:** {item['members']}")
else:
    st.warning("No data found. Check API connection.")

# --- 4. UI: HISTORY ---
with st.expander("📊 View All Raw Trades"):
    st.dataframe(df, use_container_width=True)