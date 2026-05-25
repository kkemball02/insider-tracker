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
    if not api_key: return pd.DataFrame(), "API Key Missing"
    
    # FIXED: Reverted to the strict Free Tier limits (page=0, limit=100)
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json()), None
        else:
            return pd.DataFrame(), f"HTTP {response.status_code}: {response.text}"
    except Exception as e: 
        return pd.DataFrame(), f"Connection Error: {e}"

# --- HELPER: TRANSACTION MAPPER ---
def get_transaction_label(t_type):
    t = str(t_type).upper()
    if 'P' in t: return "Buy", "#00FF00", "triangle-up"
    if 'S' in t: return "Sell", "#FF0000", "triangle-down"
    return "Grant", "#FFFF00", "circle"

# --- 3. USER INTERFACE ---
st.title("🎯 Insider Matrix: Signal & Risk Monitor")

if not st.secrets.get("FMP_API_KEY"):
    st.error("Missing FMP_API_KEY in Streamlit Secrets.")
    st.stop()

# --- THE REACTIVE SCAN BAR ---
min_cluster = st.slider("Minimum Insiders in Cluster (Scan Bar)", min_value=1, max_value=20, value=2, step=1)

with st.spinner("Analyzing live feeds..."):
    df, error_msg = fetch_live_signals()
    
    if df.empty:
        # If it fails, clear the cache so it doesn't get "stuck" broken for an hour
        st.cache_data.clear()
        st.error("Live data feed currently unavailable. The app's cache has been cleared so you can try again.")
        if error_msg:
            st.caption(f"**Diagnostic Info for FMP:** {error_msg}")
        st.stop()

    # Filter instantly based on the slider
    clusters = df.groupby('symbol').filter(lambda x: len(x['reportingName'].unique()) >= min_cluster)
    
    if clusters.empty:
        st.warning(f"No clusters found with {min_cluster} or more unique insiders in the latest 100 trades.")
        st.stop()

    ranked_tickers = clusters.groupby('symbol')['reportingName'].nunique().sort_values(ascending=False).index

    for ticker in ranked_tickers:
        ticker_data = clusters[clusters['symbol'] == ticker].copy()
        cluster_size = ticker_data['reportingName'].nunique()
        score = min(cluster_size * 2, 10)
        
        price_col = 'price' if 'price' in ticker_data.columns else 'transactionPrice'
        avg_entry = ticker_data[price_col].mean() if price_col in ticker_data.columns else 0.00
        
        with st.container(border=True):
            try:
                # Fetch Price Data
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1mo")
                if hist.empty: raise ValueError("No price data")
                
                hist.index = hist.index.tz_localize(None) 
                curr_price = hist['Close'].iloc[-1]
                
                perf = ((curr_price - avg_entry) / avg_entry) * 100 if avg_entry > 0 else 0.0
                verdict = "🟢 Momentum" if perf > 0 else "🟠 Accumulation (Value)"

                # -- UI: The Header --
                st.markdown(f"### {ticker} | Score: {score}/10")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Live Price", f"${curr_price:.2f}")
                c2.metric("Insider Avg Entry", f"${avg_entry:.2f}")
                c3.metric("Gap vs Insiders", f"{perf:.1f}%")
                c4.write(f"**Trend:** {verdict}")
                
                shares_to_buy = calculate_shares(curr_price)
                st.success(f"**Trade Blueprint:** Buy **{shares_to_buy} shares** (${(shares_to_buy * curr_price):.2f}). Max Risk: ${max_risk_amount:.2f}.")
                
                # -- UI: The Interactive Chart & Table --
                with st.expander(f"📈