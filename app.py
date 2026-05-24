import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Insider Matrix Pro", layout="centered")

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

# --- LIVE SEC DATA SCRAPER ---
@st.cache_data(ttl=3600)  # Caches the data for 1 hour so the site doesn't ban your server
def fetch_live_sec_data():
    # Scrapes the last 14 days of confirmed cluster buys from OpenInsider
    url = "http://openinsider.com/screener?fd=14&xp=1&xc=1"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        dfs = pd.read_html(res.text)
        for df in dfs:
            if 'Ticker' in df.columns and 'Insider Name' in df.columns:
                return df[['Ticker', 'Trade Date', 'Insider Name', 'Title', 'Price', 'Value']]
    except:
        pass
    return pd.DataFrame()

def process_live_market(min_size):
    df = fetch_live_sec_data()
    if df.empty: return []
    
    results = []
    # Group the raw data by company to find the executive clusters
    for ticker, group in df.groupby('Ticker'):
        execs = group['Insider Name'].nunique()
        if execs >= min_size:
            try:
                live_px = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            except:
                live_px = float(group['Price'].iloc[0].replace('$', '').replace(',', ''))
                
            avg_buy = group['Price'].replace('[\$,]', '', regex=True).astype(float).mean()
            
            exec_list = []
            for _, row in group.drop_duplicates(subset=['Insider Name']).iterrows():
                exec_list.append({"name": row['Insider Name'], "role": row['Title'], "value": row['Value']})
                
            results.append({
                "ticker": ticker, 
                "size": execs, 
                "price": live_px, 
                "buy_px": avg_buy,
                "move": ((live_px - avg_buy) / avg_buy) * 100, 
                "execs": exec_list
            })
    # Sort the final list by the size of the executive cluster
    return sorted(results, key=lambda x: x['size'], reverse=True)

# --- USER INTERFACE ---
st.markdown("### 🏛️ Insider Matrix Pro (Live SEC Feed)")
min_cluster = st.slider("Minimum Executives in Cluster", 1, 5, 2)

if st.button("Scan Live Market", use_container_width=True):
    with st.spinner("Scraping live OpenInsider data (this takes a few seconds)..."):
        items = process_live_market(min_cluster)
        
    if not items:
        st.warning("No active clusters found in the last 14 days matching your criteria.")
        
    for item in items:
        with st.container(border=True):
            st.markdown(f"### {item['ticker']} | 👥 {item['size']} Core Executives")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Live Price", f"${item['price']:.2f}")
            c2.metric("Exec Avg Buy", f"${item['buy_px']:.2f}")
            c3.metric("Gap Move", f"{item['move']:.1f}%")
            
            shares = calculate_shares(item['price'])
            st.success(f"**Trade Blueprint:** Buy **{shares} shares** (${(shares*item['price']):.2f}). Stop-loss cuts you out at exactly ${max_risk_amount:.2f} lost.")
            
            with st.expander(f"📈 View 30-Day Chart"):
                try:
                    st.line_chart(yf.download(item['ticker'], period="1mo", interval="1d", progress=False)['Close'])
                except:
                    st.error("Chart data unavailable.")
                    
            st.markdown("**Cluster Breakdown:**")
            for ex in item['execs']:
                st.markdown(f"- **{ex['name']}** ({ex['role']}): Bought {ex['value']}")