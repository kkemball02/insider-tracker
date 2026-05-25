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
                with st.expander(f"📈 Interactive Chart & Buyer Log for {ticker}", expanded=True):
                    
                    # BUILD PLOTLY CHART
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'], 
                        low=hist['Low'], close=hist['Close'], name="Price action"
                    )])
                    
                    # OVERLAY INSIDER TRADES
                    for _, trade in ticker_data.iterrows():
                        t_date = pd.to_datetime(trade['transactionDate'])
                        trade_price = trade.get(price_col, 0)
                        
                        if trade_price == 0 or pd.isna(trade_price):
                            if t_date in hist.index: trade_price = hist.loc[t_date, 'Close']
                            else: trade_price = curr_price
                                
                        label, color, symbol = get_transaction_label(trade['transactionType'])
                        full_name = trade['reportingName']
                        shares_traded = trade.get('amount', 0)
                        total_value = shares_traded * trade_price
                        
                        hover_html = (
                            f"<b>{full_name}</b><br>"
                            f"Action: {label}<br>"
                            f"Shares: {shares_traded:,.0f}<br>"
                            f"Avg Price: ${trade_price:.2f}<br>"
                            f"Total Value: ${total_value:,.2f}<extra></extra>"
                        )
                        
                        fig.add_trace(go.Scatter(
                            x=[t_date], y=[trade_price],
                            mode='markers',
                            marker=dict(color=color, size=16, symbol=symbol, line=dict(width=2, color='black')),
                            hovertemplate=hover_html,
                            name=label
                        ))

                    fig.update_layout(
                        template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0),
                        xaxis_title="Date", yaxis_title="Price",
                        xaxis=dict(tickformat="%b %d", showgrid=False),
                        showlegend=False, hovermode="closest"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # --- DATA TABLE ---
                    st.markdown("### 📋 Transaction Log")
                    
                    display_df = ticker_data[['reportingName', 'transactionType', 'amount', price_col, 'transactionDate']].copy()
                    display_df['Total Value'] = display_df['amount'] * display_df[price_col]
                    
                    display_df['transactionType'] = display_df['transactionType'].apply(lambda x: get_transaction_label(x)[0])
                    display_df.rename(columns={
                        'reportingName': 'Insider',
                        'transactionType': 'Action',
                        'amount': 'Shares',
                        price_col: 'Price',
                        'transactionDate': 'Date'
                    }, inplace=True)
                    
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Insider": st.column_config.TextColumn("Executive Name", width="medium"),
                            "Action": st.column_config.TextColumn("Action", width="small"),
                            "Shares": st.column_config.NumberColumn("Shares", format="%d"),
                            "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                            "Total Value": st.column_config.NumberColumn("Total Value", format="$%.2f"),
                            "Date": st.column_config.DateColumn("Date")
                        }
                    )
                    
            except Exception as e:
                st.caption(f"Visuals temporarily unavailable for {ticker}. (Log: {e})")