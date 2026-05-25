import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

# --- 1. RISK MANAGER (SIDEBAR) ---
st.sidebar.markdown("### 💰 Risk Manager")
st.sidebar.caption("Calculate exact position sizes to protect your capital.")
account_size = st.sidebar.number_input("Total Account Capital ($)", min_value=100, value=5000, step=100)
risk_pct = st.sidebar.slider("Risk Tolerance Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
stop_loss_pct = st.sidebar.slider("Stop Loss Distance (%)", 1.0, 20.0, 8.0, 1.0)

# Calculate the maximum dollar amount allowed to be lost on one trade
max_risk_amount = account_size * (risk_pct / 100)
st.sidebar.info(f"**Max Risk per Trade:** ${max_risk_amount:.2f}")

def calculate_shares(price):
    risk_per_share = price * (stop_loss_pct / 100)
    return int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0

# --- 2. LIVE DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_live_signals():
    api_key = st.secrets.get("FMP_API_KEY")
    if not api_key: 
        return pd.DataFrame()
    
    # Live stable endpoint
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        return pd.DataFrame(response.json()) if response.status_code == 200 else pd.DataFrame()
    except:
        return pd.DataFrame()

# --- 3. USER INTERFACE ---
st.title("🎯 Insider Matrix: Signal & Risk Monitor")
min_cluster = st.slider("Minimum Insiders in Cluster", 1, 5, 2)

if st.button("SCAN LIVE STREAMS", type="primary", use_container_width=True):
    if not st.secrets.get("FMP_API_KEY"):
        st.error("Missing FMP_API_KEY in Streamlit Secrets.")
        st.stop()
        
    with st.spinner("Scanning live insider feeds and calculating risk..."):
        df = fetch_live_signals()
        
        if df.empty:
            st.error("Live data feed currently unavailable. Check FMP connection.")
            st.stop()

        # Group by ticker and apply cluster filter
        clusters = df.groupby('symbol').filter(lambda x: len(x['reportingName'].unique()) >= min_cluster)
        
        if clusters.empty:
            st.warning(f"No clusters with {min_cluster}+ unique insiders found right now.")
            st.stop()

        # Get unique tickers sorted by cluster size (intensity)
        ranked_tickers = clusters.groupby('symbol')['reportingName'].nunique().sort_values(ascending=False).index

        for ticker in ranked_tickers:
            ticker_data = clusters[clusters['symbol'] == ticker]
            cluster_size = ticker_data['reportingName'].nunique()
            score = min(cluster_size * 2, 10) # 1-10 Score
            
            # Use safe column selection to prevent KeyError
            price_col = 'price' if 'price' in ticker_data.columns else 'transactionPrice'
            avg_entry = ticker_data[price_col].mean() if price_col in ticker_data.columns else 0.00
            
            with st.container(border=True):
                # Safely fetch yfinance chart data
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="1mo")
                    if hist.empty: raise ValueError("No price data")
                    
                    curr_price = hist['Close'].iloc[-1]
                    
                    # Logic: Accumulation vs Momentum
                    if avg_entry > 0:
                        perf = ((curr_price - avg_entry) / avg_entry) * 100
                        verdict = "🟢 Momentum" if perf > 0 else "🟠 Accumulation (Value)"
                    else:
                        perf = 0.0
                        verdict = "⚪ Unknown Entry"

                    # -- UI: The Signal Card --
                    st.markdown(f"### {ticker} | Score: {score}/10")
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Live Price", f"${curr_price:.2f}")
                    c2.metric("Insider Avg Entry", f"${avg_entry:.2f}")
                    c3.metric("Gap vs Insiders", f"{perf:.1f}%")
                    c4.write(f"**Trend:** {verdict}")
                    
                    # -- UI: The Risk Blueprint --
                    shares_to_buy = calculate_shares(curr_price)
                    total_investment = shares_to_buy * curr_price
                    st.success(f"**Trade Blueprint:** Buy **{shares_to_buy} shares** (${total_investment:.2f} total). If your {stop_loss_pct}% stop-loss hits, you lose your exact max risk of ${max_risk_amount:.2f}.")
                    
                    # -- UI: Chart & Deep Dive --
                    with st.expander(f"📈 View Live Chart & Buyer Details for {ticker}"):
                        st.line_chart(hist['Close'])
                        st.write("**Who bought:**")
                        # Display safe columns
                        display_cols = [c for c in ['reportingName', 'transactionType', 'amount', price_col, 'transactionDate'] if c in ticker_data.columns]
                        st.dataframe(ticker_data[display_cols], hide_index=True)
                        
                except Exception as e:
                    st.markdown(f"### {ticker} | Score: {score}/10")
                    st.caption(f"Price chart temporarily unavailable for {ticker}.")