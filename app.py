import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_insider_data(api_key):
    # Using the verified stable endpoint
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")

# --- 3. UI & SCORING LOGIC ---
st.title("🎯 Insider Signal Monitor")

if st.button("SCAN FOR SIGNALS", type="primary", use_container_width=True):
    if not api_key:
        st.error("API Key missing. Add FMP_API_KEY to Streamlit Secrets.")
    else:
        with st.spinner("Analyzing market flow..."):
            df = fetch_insider_data(api_key)
            
            if df.empty:
                st.warning("No data found or connection failed.")
            else:
                # Logic: Group by Ticker, count unique insiders
                clusters = df.groupby('symbol').agg(
                    size=('reportingName', 'nunique'),
                    members=('reportingName', lambda x: ', '.join(x.unique())),
                    last_date=('transactionDate', 'max'),
                    price=('price', 'last')
                ).reset_index()
                
                # Filter: Only clusters with 2+ people
                clusters = clusters[clusters['size'] >= 2]
                
                # Scoring: Score = Cluster Size * 2 (Capped at 10)
                clusters['score'] = clusters['size'].apply(lambda x: min(x * 2, 10))
                
                # Sort: Best first
                ranked = clusters.sort_values(by='score', ascending=False)
                
                if ranked.empty:
                    st.info("No significant clusters detected right now.")
                else:
                    for _, row in ranked.iterrows():
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([1, 2, 2])
                            col1.metric("Score", f"{int(row['score'])}/10")
                            col2.markdown(f"### {row['symbol']}")
                            col3.write(f"**Cluster Size:** {row['size']} Insiders")
                            st.write(f"**Insiders:** {row['members']}")
                            st.caption(f"Last Transaction: {row['last_date']} | Price: ${row['price']:.2f}")