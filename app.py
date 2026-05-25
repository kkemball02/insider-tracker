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
    if 'P' in t: return "Buy", "lime", "triangle-up"
    if 'S' in t: return "Sell", "red", "triangle-down"
    return "Grant/Other", "yellow", "circle"

# --- 3. USER INTERFACE ---
st.title("🎯 Insider Matrix: Signal & Risk Monitor")
min_cluster = st.slider("Minimum Insiders in Cluster", 1, 5, 2)

if st.button("SCAN LIVE STREAMS", type="primary", use_container_width=True):
    if not st.secrets.get("FMP_API_KEY"):
        st.error("Missing FMP_API_KEY in Streamlit Secrets.")
        st.stop()
        
    with st.spinner("Scanning live feeds, charting overlays, and calculating risk..."):
        df = fetch_live_signals()
        if df.empty:
            st.error("Live data feed currently unavailable. Check FMP connection.")
            st.stop()

        clusters = df.groupby('symbol').filter(lambda x: len(x['reportingName'].unique()) >= min_cluster)
        if clusters.empty:
            st.warning(f"No clusters with {min_cluster}+ unique insiders found right now.")
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
                    
                    # Remove timezone to prevent Plotly matching errors with dates
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
                    
                    # -- UI: The Chart & Details Expander --
                    with st.expander(f"📈 View Live Chart & Buyer Details for {ticker}", expanded=True):
                        
                        # BUILD PLOTLY CHART
                        fig = go.Figure(data=[go.Candlestick(
                            x=hist.index, open=hist['Open'], high=hist['High'], 
                            low=hist['Low'], close=hist['Close'], name="Price"
                        )])
                        
                        # OVERLAY INSIDER TRADES
                        for _, trade in ticker_data.iterrows():
                            t_date = pd.to_datetime(trade['transactionDate'])
                            trade_price = trade.get(price_col, 0)
                            
                            # Fallback if trade price is missing (e.g. stock grant)
                            if trade_price == 0 or pd.isna(trade_price):
                                if t_date in hist.index:
                                    trade_price = hist.loc[t_date, 'Close']
                                else:
                                    trade_price = curr_price
                                    
                            label, color, symbol = get_transaction_label(trade['transactionType'])
                            last_name = str(trade['reportingName']).split()[-1] # Use last name for cleaner chart
                            
                            fig.add_trace(go.Scatter(
                                x=[t_date], y=[trade_price],
                                mode='markers+text',
                                marker=dict(color=color, size=12, symbol=symbol, line=dict(width=1, color='black')),
                                text=[f"{last_name} ({label})"],
                                textposition='top center',
                                textfont=dict(color=color, size=10),
                                name=f"{last_name} {label}"
                            ))

                        # Clean up chart layout
                        fig.update_layout(
                            template="plotly_dark",
                            margin=dict(l=0, r=0, t=30, b=0),
                            xaxis_title="Date",
                            yaxis_title="Price",
                            xaxis=dict(tickformat="%b %d", showgrid=False), # Better time markers
                            showlegend=False # Hide default legend to keep it clean
                        )
                        st.plotly_chart(fig, use_container_width=True)

                        # ENHANCED BUYER DATA
                        st.markdown("### 👥 Who is Trading?")
                        
                        # Transaction Legend
                        st.info("**Legend:** 🟢 **P-Purchase:** Open Market Buy (Strong Conviction) | 🔴 **S-Sale:** Open Market Sell | 🟡 **A-Award:** Corporate Stock Grant (Neutral)")
                        
                        # Clean and calculate data for Intuitive Table
                        display_df = ticker_data[['reportingName', 'transactionType', 'amount', price_col, 'transactionDate']].copy()
                        display_df['Total Value ($)'] = display_df['amount'] * display_df[price_col]
                        
                        # Rename columns to be human readable
                        display_df.rename(columns={
                            'reportingName': 'Insider Name',
                            'transactionType': 'Type',
                            'amount': 'Shares',
                            price_col: 'Price ($)',
                            'transactionDate': 'Date'
                        }, inplace=True)
                        
                        # Format money and numbers
                        display_df['Total Value ($)'] = display_df['Total Value ($)'].apply(lambda x: f"${x:,.2f}")
                        display_df['Shares'] = display_df['Shares'].apply(lambda x: f"{int(x):,}")
                        display_df['Price ($)'] = display_df['Price ($)'].apply(lambda x: f"${x:.2f}")
                        
                        st.dataframe(display_df, hide_index=True, use_container_width=True)
                        
                except Exception as e:
                    st.caption(f"Visuals temporarily unavailable for {ticker}. (Log: {e})")