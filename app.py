import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="Insider Matrix")

# --- 1. DATA FETCHING ---
@st.cache_data(ttl=3600)
def get_insider_data():
    api_key = st.secrets.get("FMP_API_KEY")
    url = f"https://financialmodelingprep.com/api/v3/insider-trading/latest?limit=100&apikey={api_key}"
    response = requests.get(url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()

df = get_insider_data()

# --- 2. LOGIC: SCORING & ANALYSIS ---
def analyze_signal(ticker_df, current_price):
    avg_entry = ticker_df['price'].mean()
    perf = ((current_price - avg_entry) / avg_entry) * 100
    verdict = "🟢 Good" if perf > 0 else "🟠 Accumulation"
    return verdict, perf, avg_entry

# --- 3. UI ---
st.title("🎯 Insider Signal Monitor")
if df.empty:
    st.error("Data feed unavailable.")
    st.stop()

# Grouping
clusters = df.groupby('symbol').filter(lambda x: len(x) >= 2)
tickers = clusters['symbol'].unique()

for ticker in tickers:
    ticker_data = clusters[clusters['symbol'] == ticker]
    
    with st.expander(f"### {ticker} | Insiders: {len(ticker_data)} | Status: Loading..."):
        # Get live price
        stock = yf.Ticker(ticker)
        curr_price = stock.history(period="1d")['Close'].iloc[-1]
        
        verdict, perf, avg_entry = analyze_signal(ticker_data, curr_price)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Live Price", f"${curr_price:.2f}")
        col2.metric("Performance", f"{perf:.1f}%")
        col3.write(f"**Verdict:** {verdict}")
        
        st.write(f"**Analysis:** {ticker} is showing a cluster of {len(ticker_data)} insiders. Avg entry ${avg_entry:.2f}. Expect { 'bullish momentum' if perf > 0 else 'a bottoming process'}.")
        
        # Chart
        hist = stock.history(period="3mo")
        fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
        fig.add_hline(y=avg_entry, line_dash="dash", line_color="yellow", annotation_text="Avg Insider Entry")
        fig.update_layout(template="plotly_dark", height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        # Buyer Details
        st.write("### 👥 Buyer Breakdown")
        st.dataframe(ticker_data[['reportingName', 'transactionType', 'amount', 'transactionDate']], use_container_width=True)