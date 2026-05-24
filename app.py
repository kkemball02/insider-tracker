import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Insider Matrix Pro", layout="centered")

# --- SIDEBAR: RISK MANAGER ---
st.sidebar.markdown("### 💰 Risk Manager")
account_size = st.sidebar.number_input("Total Account Capital ($)", min_value=100, value=5000, step=100)
risk_pct = st.sidebar.slider("Risk Tolerance (%)", 0.5, 5.0, 1.0, 0.5)
stop_loss_pct = st.sidebar.slider("Stop Loss Distance (%)", 1.0, 20.0, 8.0, 1.0)
max_risk_amount = account_size * (risk_pct / 100)
st.sidebar.info(f"**Max Risk per Trade:** ${max_risk_amount:.2f}")

def calculate_shares(price):
    risk_per_share = price * (stop_loss_pct / 100)
    return int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0

# --- DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_live_sec_data():
    url = "http://openinsider.com/screener?fd=14&xp=1&xc=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        dfs = pd.read_html(res.text)
        for df in dfs:
            if 'Ticker' in df.columns:
                return df[['Ticker', 'Trade Date', 'Insider Name', 'Title', 'Price', 'Value']]
    except:
        return pd.DataFrame()
    return pd.DataFrame()

# --- MAIN UI ---
st.markdown("### 🏛️ Insider Matrix Pro")
min_cluster = st.slider("Minimum Executives in Cluster", 1, 5, 2)

if st.button("Scan Live Market", use_container_width=True):
    with st.spinner("Scraping live data..."):
        df = fetch_live_sec_data()
        if df.empty:
            st.error("Could not fetch live data. Check your internet or try again later.")
        else:
            # Grouping Logic
            results = []
            for ticker, group in df.groupby('Ticker'):
                execs = group['Insider Name'].nunique()
                if execs >= min_cluster:
                    try:
                        ticker_data = yf.Ticker(ticker)
                        live_px = ticker_data.history(period="1d")['Close'].iloc[-1]
                    except:
                        live_px = 0.0
                    
                    results.append({"ticker": ticker, "size": execs, "price": live_px})
            
            if not results:
                st.warning("No clusters found for this setting.")
            else:
                for item in results:
                    with st.container(border=True):
                        st.subheader(f"{item['ticker']} - {item['size']} Executives")
                        st.metric("Live Price", f"${item['price']:.2f}")
                        shares = calculate_shares(item['price'])
                        st.success(f"Recommended Position: {shares} shares")
else:
    st.info("Click the button above to pull the latest insider filings.")