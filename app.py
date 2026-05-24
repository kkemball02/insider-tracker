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
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json())
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- 2. ANALYSIS LOGIC ---
def get_verdict(ticker, ticker_df, curr_price):
    avg_entry = ticker_df['price'].mean()
    perf = ((curr_price - avg_entry) / avg_entry) * 100
    if perf > 5: return "🟢 Momentum (Price Up)", perf
    if perf < -5: return "🟠 Accumulation (Value Play)", perf
    return "⚪ Neutral", perf

# --- 3. UI ---
st.title("🎯 Insider Matrix: Signal Monitor")
df = fetch_insider_data()

if df.empty:
    st.error("No recent insider data found. (API limit or empty feed).")
    st.stop()

# Grouping logic
clusters = df.groupby('symbol').filter(lambda x: len(x) >= 2)
ranked_tickers = clusters.groupby('symbol').size().sort_values(ascending=False).index

selected_ticker = st.selectbox("Select a High-Signal Stock", ranked_tickers)

# Processing Selected Stock
ticker_data = clusters[clusters['symbol'] == selected_ticker]
stock = yf.Ticker(selected_ticker)
try:
    hist = stock.history(period="3mo")
    curr_price = hist['Close'].iloc[-1]
    
    verdict, perf = get_verdict(selected_ticker, ticker_data, curr_price)
    
    # Dashboard Layout
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Price", f"${curr_price:.2f}")
    col2.metric("Performance vs Insiders", f"{perf:.1f}%")
    col3.write(f"**Verdict:** {verdict}")
    
    # Chart
    fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
    fig.add_hline(y=ticker_data['price'].mean(), line_dash="dash", line_color="yellow", annotation_text="Insider Avg")
    fig.update_layout(template="plotly_dark", title=f"{selected_ticker} Price Action")
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed Buyer Info
    st.write("### 👥 Who is buying?")
    st.dataframe(ticker_data[['reportingName', 'transactionType', 'amount', 'price', 'transactionDate']], use_container_width=True)

except Exception as e:
    st.warning("Could not pull chart data for this ticker.")