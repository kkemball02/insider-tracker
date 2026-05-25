import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

# --- 1. RISK MANAGER (SIDEBAR) ---
st.sidebar.markdown("### 💰 Risk Manager")
st.sidebar.caption("Calculate exact position sizes to protect your capital.")
account_size = st.sidebar.number_input("Total Account Capital ($)", min_value=100, value=5000, step=100)
risk_pct = st.sidebar.slider("Risk Tolerance Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
stop_loss_pct = st.sidebar.slider("Stop Loss Distance (%)", 1.0, 20.0, 8.0, 1.0)

max_risk_amount = account_size * (risk_pct / 100)
st.sidebar.info(f"**Max Risk per Trade:** ${max_risk_amount:.2f}")

def calculate_shares(price):
    risk_per_share = price * (stop_loss_pct / 100)
    return int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0

# --- 2. LIVE DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_live_signals():
    api_key = st.secrets.get("FMP_API_KEY")
    if not api_key: return pd.DataFrame()
    
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- HELPER: TRANSACTION MAPPER ---
def get_transaction_label(t_type):
    t = str(t_type).upper()
    if 'P' in t: return "Buy", "#00FF00", "triangle-up" # Bright Green
    if 'S' in t: return "Sell", "#FF0000", "triangle-down" # Bright Red
    return "Grant", "#FFFF00", "circle" # Yellow

# --- 3. USER INTERFACE ---
st.title("🎯 Insider Matrix: Signal & Risk Monitor")
min_cluster = st.slider("Minimum Insiders in Cluster", 1, 5, 2)

if st.button("SCAN LIVE STREAMS", type="primary", use_container_width=True):
    if not st.secrets.get("FMP_API_KEY"):
        st.error("Missing FMP_API_KEY in Streamlit Secrets.")
        st.stop()
        
    with st.spinner("Scanning live feeds, building interactive charts, and calculating risk..."):
        df = fetch_live_signals()