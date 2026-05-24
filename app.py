import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Insider Matrix Pro")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_insider_data():
    api_key = st.secrets.get("FMP_API_KEY")
    # Using the stable endpoint
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

# --- 2. UI ---
st.title("🎯 Insider Matrix: Signal Monitor")
df = fetch_insider_data()

if df.empty:
    st.error("No recent insider data found. Check your API connection.")
    st.stop()

# Ranking Logic
clusters = df.groupby('symbol').filter(lambda x: len(x) >= 2)
if clusters.empty:
    st.warning("No clusters with 2+ insiders found in the latest batch.")
    st.stop()

ranked_tickers = clusters.groupby('symbol').size().sort_values(ascending=False).index
selected_ticker = st.selectbox("Select a High-Signal Stock", ranked_tickers)

# Processing
ticker_data = clusters[clusters['symbol'] == selected_ticker]
stock = yf.Ticker(selected_ticker)

# -- SAFE CHARTING --
try:
    hist = stock.history(period="3mo")
    if hist.empty:
        raise ValueError("No historical price data.")
    
    curr_price = hist['Close'].iloc[-1]
    avg_entry = ticker_data['price'].mean()
    perf = ((curr_price - avg_entry) / avg_entry) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Price", f"${curr_price:.2f}")
    col2.metric("Performance vs Insiders", f"{perf:.1f}%")
    col3.write(f"**Verdict:** {'🟢 Bullish' if perf > 0 else '🟠 Accumulation'}")
    
    # Plotly Chart
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.add_hline(y=avg_entry, line_dash="dash", line_color="yellow", annotation_text="Insider Avg")
    fig.update_layout(template="plotly_dark", title=f"{selected_ticker} Price Action")
    st.plotly_chart(fig, use_container_width=True)
    
except Exception as e:
    st.info(f"Chart data currently unavailable for {selected_ticker}. (System log: {e})")

# Buyer Breakdown
st.write("### 👥 Buyer Breakdown")
st.dataframe(ticker_data[['reportingName', 'transactionType', 'amount', 'price', 'transactionDate']], use_container_width=True)