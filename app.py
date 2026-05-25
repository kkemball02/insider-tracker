import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

# ==========================================
# --- SIDEBAR: CONTROLS & RISK MANAGER ---
# ==========================================
st.sidebar.title("⚙️ Dashboard Controls")

# 1. Scanner Settings (Moved here so it never disappears)
st.sidebar.markdown("### 1. Scanner Settings")
st.sidebar.caption("Filter the live data feed.")
min_cluster = st.sidebar.slider("Minimum Insiders in Cluster", min_value=1, max_value=20, value=2, step=1)

# 2. Risk Manager
st.sidebar.markdown("### 2. Risk Manager")
st.sidebar.caption("Calculate exact position sizes to protect your capital.")
account_size = st.sidebar.number_input("Total Account Capital ($)", min_value=100, value=5000, step=100)
risk_pct = st.sidebar.slider("Risk Tolerance Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
stop_loss_pct = st.sidebar.slider("Stop Loss Distance (%)", 1.0, 20.0, 8.0, 1.0)

max_risk_amount = account_size * (risk_pct / 100)
st.sidebar.info(f"**Max Risk per Trade:** ${max_risk_amount:.2f}")

def calculate_shares(price):
    if price <= 0: return 0
    risk_per_share = price * (stop_loss_pct / 100)
    return int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0


# ==========================================
# --- LIVE DATA ENGINE ---
# ==========================================
@st.cache_data(ttl=3600)
def fetch_live_signals():
    api_key = st.secrets.get("FMP_API_KEY")
    if not api_key: return pd.DataFrame(), "API Key Missing"
    
    # Strict Free Tier limits
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json()), None
        else:
            return pd.DataFrame(), f"HTTP {response.status_code}: {response.text}"
    except Exception as e: 
        return pd.DataFrame(), f"Connection Error: {e}"

def get_transaction_label(t_type):
    t = str(t_type).upper()
    if 'P' in t: return "Buy", "#00FF00", "triangle-up"
    if 'S' in t: return "Sell", "#FF0000", "triangle-down"
    return "Grant", "#FFFF00", "circle"


# ==========================================
# --- MAIN USER INTERFACE ---
# ==========================================
st.title("🎯 Insider Matrix: Signal & Risk Monitor")

# API Key Check
if not st.secrets.get("FMP_API_KEY"):
    st.error("Missing FMP_API_KEY in Streamlit Secrets.")
    st.info("To fix this, go to your Streamlit dashboard -> App Settings -> Secrets, and make sure your key is added.")
    st.stop()

# Main Data Processing
with st.spinner("Analyzing live feeds..."):
    df, error_msg = fetch_live_signals()
    
    if df.empty:
        st.cache_data.clear()
        st.error("Live data feed currently unavailable. The app's cache has been cleared so you can try again.")
        if error_msg:
            st.caption(f"**Diagnostic Info for FMP:** {error_msg}")
        st.stop()

    # Filter instantly based on the slider in the sidebar
    clusters = df.groupby('symbol').filter(lambda x: len(x['reportingName'].unique()) >= min_cluster)
    
    if clusters.empty:
        st.warning(f"No clusters found with {min_cluster} or more unique insiders in the latest batch. Try lowering the 'Minimum Insiders' slider in the sidebar.")
        st.stop()

    ranked_tickers = clusters.groupby('symbol')['reportingName'].nunique().sort_values(ascending=False).index

    for ticker in ranked_tickers:
        ticker_data = clusters[clusters['symbol'] == ticker].copy()
        cluster_size = ticker_data['reportingName'].nunique()
        score = min(cluster_size * 2, 10)
        
        price_col =