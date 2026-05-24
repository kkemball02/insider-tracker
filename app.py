import streamlit as st
import pandas as pd
import yfinance as yf
import requests

# --- PAGE SETUP ---
st.set_page_config(page_title="Insider Matrix", layout="centered")

# --- RISK MANAGER (SIDEBAR) ---
st.sidebar.markdown("### 💰 Risk Manager")
account_size = st.sidebar.number_input("Total Account Capital ($)", min_value=100, value=5000, step=100)
risk_pct = st.sidebar.slider("Risk Tolerance Per Trade (%)", 0.5, 5.0, 1.0, 0.5)
stop_loss_pct = st.sidebar.slider("Stop Loss Distance (%)", 1.0, 20.0, 8.0, 1.0)
max_risk_amount = account_size * (risk_pct / 100)
st.sidebar.info(f"**Max Risk per Trade:** ${max_risk_amount:.2f}")

def calculate_shares(price):
    risk_per_share = price * (stop_loss_pct / 100)
    return int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0

# --- LIVE DATA ENGINE ---
# We cache the data for 1 hour so we don't get banned from the server for spamming requests
@st.cache_data(ttl=3600) 
def fetch_live_clusters():
    try:
        # Scrape last 7 days of open market buys
        url = "http://openinsider.com/screener?s=&o=&pl=&ph=&ll=&lh=&fd=7&fdr=&td=0&tdr=&fdlyl=&fdlyh=&daysago=&xp=1&xs=1&vl=&vh=&ocl=&och=&sic1=-1&sicl=100&sich=9999&grp=0&nfl=&nfh=&nil=&nih=&nol=&noh=&v2l=&v2h=&oc2l=&oc2h=&sortcol=0&cnt=100&page=1"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        
        # Parse the HTML to find the data tables
        dfs = pd.read_html(response.text)
        df = next((table for table in dfs if 'Ticker' in table.columns), pd.DataFrame())
        
        if df.empty: return []

        results = []
        # Group by Ticker to find multiple buyers (Clusters)
        for ticker, group in df.groupby('Ticker'):
            unique_buyers = group['Insider Name'].nunique()
            
            if unique_buyers >= 2: # Keep 2 as absolute minimum to scan
                live_price = group['Price'].replace({r'\$': '', ',': ''}, regex=True).astype(float).iloc[0]
                
                # Fetch live chart data and RSI via Yahoo Finance
                try:
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="3mo")
                    if not hist.empty:
                        real_price = float(hist['Close'].iloc[-1])
                        # Calculate 14-day RSI (Momentum)
                        delta = hist['Close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                        rs = gain / loss
                        rsi = float(100 - (100 / (1 + rs)).iloc[-1])
                    else:
                        real_price, rsi = live_price, 50.0
                except:
                    real_price, rsi = live_price, 50.0

                execs = []
                for _, row in group.drop_duplicates(subset=['Insider Name']).iterrows():
                    execs.append({
                        "name": str(row['Insider Name']),
                        "role": str(row['Title']),
                        "value": str(row['Value'])
                    })
                    
                results.append({
                    "ticker": ticker,
                    "size": unique_buyers,
                    "price": real_price,
                    "rsi": rsi,
                    "execs": execs
                })
                
        return sorted(results, key=lambda x: x['size'], reverse=True)
    except Exception as e:
        return []

# --- UI INTERFACE ---
st.markdown("### 🏛️ Insider Matrix Pro (LIVE)")
min_cluster = st.slider("Minimum Executives in Cluster", 2, 10, 3)

if st.button("Scan Live Market", use_container_width=True):
    with st.spinner("Scraping SEC Filings & Live Markets..."):
        items = fetch_live_clusters()
        
    filtered_items = [i for i in items if i['size'] >= min_cluster]
    
    if not filtered_items:
        st.warning("No live clusters found matching your criteria right now. The market might be quiet, or executives are in an earnings blackout period.")
        
    for item in filtered_items:
        badge = "🟢" if item['size'] >= 3 else "🟠"
        
        with st.container(border=True):
            st.markdown(f"### {item['ticker']} {badge} ({item['size']} Executives)")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Live Price", f"${item['price']:.2f}")
            c2.metric("14-Day RSI", f"{item['rsi']:.1f}")
            c3.metric("Cluster Size", item['size'])
            
            # The Technical Indicator Fail-Safe
            if item['rsi'] > 70:
                st.warning("⚠️ **Technical Warning:** Stock is heavily overbought (RSI > 70). Buying right now carries high pullback risk.")
            elif item['rsi'] < 30:
                st.success("✅ **Technical Bonus:** Stock is oversold (RSI < 30). Insiders are aggressively buying the bottom.")
            
            # Position Sizer
            shares_to_buy = calculate_shares(item['price'])
            st.info(f"**Trade Blueprint:** Buy **{shares_to_buy} shares** (${(shares_to_buy * item['price']):.2f} total). If your {stop_loss_pct}% stop-loss hits, you lose exactly your max risk of ${max_risk_amount:.2f}.")
            
            # Live Interactive Chart
            with st.expander(f"📈 View 30-Day Live Chart for {item['ticker']}"):
                try:
                    stock_chart = yf.Ticker(item['ticker'])
                    hist = stock_chart.history(period="1mo")
                    if not hist.empty:
                        st.line_chart(hist['Close'])
                    else:
                        st.error("Chart data unavailable.")
                except:
                    st.error("Chart data unavailable.")
                    
            # Who bought what
            st.markdown("**👥 Core Executives Buying:**")
            for ex in item['execs']:
                st.markdown(f"- **{ex['name']}** ({ex['role']}): Bought {ex['value']}")