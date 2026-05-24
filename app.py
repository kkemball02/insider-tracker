import streamlit as st
import pandas as pd
import yfinance as yf
import requests

st.set_page_config(page_title="Insider Matrix Pro", layout="wide")

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
@st.cache_data(ttl=3600)
def fetch_live_sec_data():
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
    return sorted(results, key=lambda x: x['size'], reverse=True)

# --- USER INTERFACE & TABS ---
st.markdown("### 🏛️ Insider Matrix Pro")

tab_live, tab_history = st.tabs(["🔴 Live Market Scanner", "📚 The Playbook (History)"])

# --- TAB 1: LIVE SCANNER ---
with tab_live:
    st.caption("Scraping live SEC filings for the last 14 days.")
    
    # THE NEW TOGGLE CHECKBOX
    show_all = st.checkbox("Show all insider trades (Ignore cluster size)", value=False)
    
    if show_all:
        min_cluster = 1
        st.info("Showing all single and multi-executive buys.")
    else:
        min_cluster = st.slider("Minimum Executives in Cluster", 1, 5, 2)

    if st.button("Scan Live Market", use_container_width=True):
        with st.spinner("Scraping live OpenInsider data..."):
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

# --- TAB 2: HISTORICAL ANALYSIS ---
with tab_history:
    st.markdown("### 📖 Historical Cluster Analysis")
    st.caption("Reviewing past setups to understand why trades succeed or fail.")
    
    with st.container(border=True):
        st.markdown("#### 🏆 SUCCESS: Meta Platforms (META) - Nov 2022")
        c1, c2, c3 = st.columns(3)
        c1.metric("Cluster Size", "4 Executives")
        c2.metric("Avg Entry Price", "$95.00")
        c3.metric("Peak Return", "+426%")
        st.success("**Why it worked:** Meta was at multi-year lows. The RSI was deeply oversold. The broader market was bottoming, and the executives bought heavily right before announcing a massive 'Year of Efficiency'.")
        with st.expander("📈 View META Chart (Sept 2022 - April 2023)"):
            try:
                st.line_chart(yf.download('META', start='2022-09-01', end='2023-04-01', progress=False)['Close'])
            except:
                st.error("Chart data unavailable.")

    with st.container(border=True):
        st.markdown("#### 💀 VALUE TRAP: Intel (INTC) - Jan 2024")
        c1, c2, c3 = st.columns(3)
        c1.metric("Cluster Size", "CEO Heavy Buy")
        c2.metric("Avg Entry Price", "$43.50")
        c3.metric("Drawdown", "-50%+")
        st.error("**Why it failed:** The CEO bought the 'dip' after a bad earnings report, but the stock was violating major technical support. Buying a broken chart just because an insider bought is a trap.")
        with st.expander("📉 View INTC Chart (Nov 2023 - Aug 2024)"):
            try:
                st.line_chart(yf.download('INTC', start='2023-11-01', end='2024-08-01', progress=False)['Close'])
            except:
                st.error("Chart data unavailable.")