import streamlit as st
import pandas as pd
import yfinance as yf
import requests
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

# ==========================================
# --- SIDEBAR: CONTROLS & RISK MANAGER ---
# ==========================================
st.sidebar.title("⚙️ Dashboard Controls")

st.sidebar.markdown("### 1. Scanner Settings")
min_cluster = st.sidebar.slider("Minimum Insiders in Cluster", min_value=1, max_value=20, value=2, step=1)

st.sidebar.markdown("### 2. Risk Manager")
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
# --- INSIGHT ENGINE (HEURISTICS) ---
# ==========================================
def get_role_summary(owner_type, name):
    owner = str(owner_type).lower()
    if 'ceo' in owner or 'chief executive' in owner: return "🏢 **Chief Executive Officer:** The highest conviction signal. They control the exact trajectory of the company."
    if 'cfo' in owner or 'financial' in owner: return "📊 **Chief Financial Officer:** Excellent signal for valuation. They know the exact balance sheet and upcoming earnings."
    if 'director' in owner: return "🪑 **Board Director:** Strong macro-level view of the company's strategic direction and potential acquisitions."
    if '10%' in owner: return "🐋 **Major Shareholder (10%+):** Institutional or 'whale' money. Indicates heavy accumulation or distribution."
    return "👔 **Corporate Insider:** Standard executive access to non-public operational data."

def get_trade_motive(t_type, is_buy):
    if is_buy: return "Open market purchase using personal capital. This strongly indicates the insider believes the stock is currently undervalued and expects a rally."
    if 'S' in str(t_type).upper(): return "Open market sale. This can indicate profit-taking, tax harvesting, or a personal need for liquidity. While negative, it does not always mean the company is failing."
    return "Corporate Stock Grant/Award. This is standard executive compensation. It is a neutral signal because no personal capital was risked."

def get_timing_motive(trade_price, curr_price, is_buy):
    if not is_buy: return "Exited position at this price level."
    if trade_price == 0: return "Received via corporate action (No cost basis)."
    
    diff = ((curr_price - trade_price) / trade_price) * 100
    if diff > 5: return f"🟢 **Brilliant Timing:** They bought the dip significantly below current market levels. You are currently paying a {diff:.1f}% premium compared to them."
    if diff < -5: return f"🟠 **Premium Entry:** They bought *higher* than current levels (you are getting a {-diff:.1f}% discount!). This suggests they expect a massive future breakout."
    return "⚪ **Market-Level Entry:** They bought right near current consolidation zones, suggesting they believe this is the floor."

def get_transaction_label(t_type):
    t = str(t_type).upper()
    if 'P' in t: return "Buy", "#00FF00", "triangle-up"
    if 'S' in t: return "Sell", "#FF0000", "triangle-down"
    return "Grant", "#FFFF00", "circle"

# ==========================================
# --- LIVE DATA ENGINE ---
# ==========================================
@st.cache_data(ttl=3600)
def fetch_live_signals():
    api_key = st.secrets.get("FMP_API_KEY")
    if not api_key: return pd.DataFrame(), "API Key Missing"
    
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return pd.DataFrame(response.json()), None
        return pd.DataFrame(), f"HTTP {response.status_code}: {response.text}"
    except Exception as e: 
        return pd.DataFrame(), f"Connection Error: {e}"

# ==========================================
# --- MAIN USER INTERFACE ---
# ==========================================
st.title("🎯 Insider Matrix: Signal & Risk Monitor")

if not st.secrets.get("FMP_API_KEY"):
    st.error("Missing FMP_API_KEY in Streamlit Secrets.")
    st.stop()

with st.spinner("Analyzing live feeds..."):
    df, error_msg = fetch_live_signals()
    
    if df.empty:
        st.cache_data.clear()
        st.error("Live data feed currently unavailable. The app's cache has been cleared so you can try again.")
        st.stop()

    clusters = df.groupby('symbol').filter(lambda x: len(x['reportingName'].unique()) >= min_cluster)
    if clusters.empty:
        st.warning(f"No clusters found with {min_cluster}+ unique insiders. Try lowering the slider in the sidebar.")
        st.stop()

    ranked_tickers = clusters.groupby('symbol')['reportingName'].nunique().sort_values(ascending=False).index

    for ticker in ranked_tickers:
        ticker_data = clusters[clusters['symbol'] == ticker].copy()
        cluster_size = ticker_data['reportingName'].nunique()
        score = min(cluster_size * 2, 10)
        
        price_col = 'price' if 'price' in ticker_data.columns else 'transactionPrice'
        avg_entry = ticker_data[ticker_data['transactionType'].str.contains('P', case=False, na=False)][price_col].mean()
        if pd.isna(avg_entry): avg_entry = ticker_data[price_col].mean()
        
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

                # -- UI: Header --
                st.markdown(f"## {ticker} | Conviction Score: {score}/10")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Live Price", f"${curr_price:.2f}")
                c2.metric("Insider Avg Buy", f"${avg_entry:.2f}")
                c3.metric("Your Gap vs Insiders", f"{perf:.1f}%")
                c4.write(f"**Trend:** {verdict}")
                
                shares_to_buy = calculate_shares(curr_price)
                st.success(f"**Trade Blueprint:** Buy **{shares_to_buy} shares** (${(shares_to_buy * curr_price):.2f}). Max Risk: ${max_risk_amount:.2f}.")
                
                # --- TWO TABS FOR CLEANLINESS ---
                tab1, tab2 = st.tabs(["📈 Clean Price Chart", "🕵️ Insider Dossiers & Motives"])
                
                with tab1:
                    # BUILD PLOTLY CHART
                    fig = go.Figure(data=[go.Candlestick(
                        x=hist.index, open=hist['Open'], high=hist['High'], 
                        low=hist['Low'], close=hist['Close'], name="Price action"
                    )])
                    
                    # Un-bunching: Aggregate trades on the same day for the chart
                    chart_data = ticker_data.copy()
                    chart_data['Date'] = pd.to_datetime(chart_data['transactionDate']).dt.date
                    
                    for date, group in chart_data.groupby('Date'):
                        t_date = pd.to_datetime(date)
                        if t_date in hist.index: trade_price = hist.loc[t_date, 'Close']
                        else: trade_price = curr_price
                        
                        # Determine dominant action of the day
                        buys = group[group['transactionType'].str.contains('P', na=False, case=False)]
                        label, color, symbol = get_transaction_label('P') if not buys.empty else get_transaction_label('S')
                        
                        names = "<br>".join(group['reportingName'].unique())
                        total_shares = group['amount'].sum()
                        
                        hover_html = f"<b>{len(group)} Trade(s) on {date}</b><br>Shares: {total_shares:,.0f}<br><b>Insiders:</b><br>{names}<extra></extra>"
                        
                        fig.add_trace(go.Scatter(
                            x=[t_date], y=[trade_price],
                            mode='markers',
                            marker=dict(color=color, size=14, symbol=symbol, line=dict(width=1, color='black'), opacity=0.8),
                            hovertemplate=hover_html,
                            name=label
                        ))

                    fig.update_layout(
                        template="plotly_dark", height=400, margin=dict(l=0, r=0, t=10, b=0),
                        xaxis=dict(
                            tickformat="%b %d", showgrid=False, 
                            rangebreaks=[dict(bounds=["sat", "mon"])] # Hide weekends to stop bunching
                        ),
                        showlegend=False, hovermode="closest"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with tab2:
                    # --- THE INSIDER DOSSIER ---
                    unique_insiders = ticker_data['reportingName'].unique()
                    selected_insider = st.selectbox("Select an Insider to view their Dossier:", unique_insiders, key=f"sel_{ticker}")
                    
                    insider_trades = ticker_data[ticker_data['reportingName'] == selected_insider].copy()
                    
                    # Determine Role
                    owner_type = insider_trades['typeOfOwner'].iloc[0] if 'typeOfOwner' in insider_trades.columns else "Corporate Insider"
                    st.info(get_role_summary(owner_type, selected_insider))
                    
                    # Clean specific table
                    insider_trades['Action'] = insider_trades['transactionType'].apply(lambda x: get_transaction_label(x)[0])
                    insider_trades['Total Value'] = insider_trades['amount'] * insider_trades[price_col]
                    
                    display_cols = ['Action', 'amount', price_col, 'Total Value', 'transactionDate']
                    safe_cols = [c for c in display_cols if c in insider_trades.columns]
                    
                    st.dataframe(
                        insider_trades[safe_cols],
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Action": st.column_config.TextColumn("Action"),
                            "amount": st.column_config.NumberColumn("Shares", format="%d"),
                            price_col: st.column_config.NumberColumn("Price", format="$%.2f"),
                            "Total Value": st.column_config.NumberColumn("Total Value", format="$%.2f"),
                            "transactionDate": st.column_config.DateColumn("Date")
                        }
                    )
                    
                    # THE "WHY" AND "WHEN" TABS
                    st.write("### 🧠 Insight Engine")
                    for _, trade in insider_trades.iterrows():
                        action = get_transaction_label(trade['transactionType'])[0]
                        is_buy = action == "Buy"
                        t_price = trade.get(price_col, 0)
                        t_date = str(trade['transactionDate'])[:10]
                        
                        with st.expander(f"Analysis: {action} on {t_date}"):
                            st.write(f"**What (Motive):** {get_trade_motive(trade['transactionType'], is_buy)}")
                            st.write(f"**When (Timing):** {get_timing_motive(t_price, curr_price, is_buy)}")

            except Exception as e:
                st.error(f"Visuals temporarily unavailable for {ticker}. (Log: {e})")