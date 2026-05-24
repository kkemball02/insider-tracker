import streamlit as st
import pandas as pd
import requests
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

# --- 1. DATA ENGINES ---
@st.cache_data(ttl=3600)
def fetch_insider_trades(api_key):
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

def get_stock_history(ticker):
    # Get 3 months of price data for context
    df = yf.download(ticker, period="3mo", progress=False)
    # Flatten multi-index columns if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")
if not api_key:
    st.error("Add FMP_API_KEY to Streamlit Secrets.")
    st.stop()

# --- 3. LOGIC ---
st.markdown("### 🏛️ Insider Matrix: Price Comparison")
df = fetch_insider_trades(api_key)

if not df.empty:
    # Get unique symbols from the latest insider trades
    symbols = df['symbol'].unique()
    selected_ticker = st.selectbox("Select Ticker to Analyze", symbols)
    
    # Filter trades for this ticker
    ticker_trades = df[df['symbol'] == selected_ticker]
    
    # Get Price Data
    hist = get_stock_history(selected_ticker)
    
    # Charting
    fig = go.Figure(data=[go.Candlestick(
        x=hist.index, open=hist['Open'], high=hist['High'], 
        low=hist['Low'], close=hist['Close']
    )])
    
    # Add Insider Trades as Markers
    for _, trade in ticker_trades.iterrows():
        trade_date = pd.to_datetime(trade['transactionDate'])
        # Add a dot for the trade
        fig.add_trace(go.Scatter(
            x=[trade_date], y=[trade.get('price', hist['Close'].mean())],
            mode='markers+text',
            name=f"{trade['reportingName']} ({trade['transactionType']})",
            marker=dict(size=12, symbol='star', color='yellow' if 'P' in trade['transactionType'] else 'red'),
            text=[trade['reportingName']], textposition="top center"
        ))
    
    fig.update_layout(template="plotly_dark", title=f"Price vs Insider Trades: {selected_ticker}")
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(ticker_trades, use_container_width=True)
else:
    st.warning("No data found.")