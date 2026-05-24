import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Signal Monitor", layout="wide")

# --- 1. DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_insider_data(api_key):
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. LOGIC: SCORING ENGINE ---
def get_ranked_signals(df):
    if df.empty: return pd.DataFrame()
    
    # Cluster = Group by Ticker
    clusters = df.groupby('symbol').agg(
        size=('reportingName', 'nunique'),
        members=('reportingName', lambda x: ', '.join(x.unique())),
        last_date=('transactionDate', 'max'),
        price=('price', 'last')
    ).reset_index()
    
    # Filter for meaningful clusters (2+ people)
    clusters = clusters[clusters['size'] >= 2]
    
    # Score = Size * 2 (capped at 10)
    clusters['score'] = clusters['size'].apply(lambda x: min(x * 2, 10))
    
    # Return sorted by score
    return clusters.sort_values(by='score', ascending=False)

# --- 3. UI ---
st.title("🎯 Insider Signal Monitor")
api_key = st.secrets.get("FMP_API_KEY")

if st.button("SCAN FOR SIGNALS", type="primary", use_container_width=True):
    if not api_key:
        st.error("Add FMP_API_KEY to Streamlit Secrets.")
    else:
        with st.spinner("Analyzing market flow..."):
            df = get_insider_data(api_key)
            signals = get_ranked_signals(df)
            
            if signals.empty:
                st.warning("No significant clusters detected right now.")
            else:
                for _, row in signals.iterrows():
                    with st.container(border=True):
                        col1, col2, col3 = st.columns([1, 2, 2])
                        col1.metric("Score", f"{int(row['score'])}/10")
                        col2.markdown(f"### {row['symbol']}")
                        col3.write(f"**Cluster Size:** {row['size']} Insiders")
                        st.write(f"**Who:** {row['members']}")
                        st.caption(f"Last Transaction: {row['last_date']}")