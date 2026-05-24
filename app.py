import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# Set page layout to wide for the sidebar
st.set_page_config(page_title="Insider Matrix", layout="centered")

# --- RISK MANAGER (SIDEBAR) ---
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


# --- DATA ENGINE ---
def run_math_engine(min_size):
    # Simulated database with technical fail-safes
    results = [
        {
            "ticker": "SOFI", "score": 8.5, "size": 3, "move": 4.5, "price": 7.42, 
            "rsi": 42, "trend": "🟢 Upward", "sector_perf": "+2.1%",
            "analysis": "High-density buying across 3 core executives during a slight dip suggests confidence in upcoming Q3 guidance. Coordinated SOFI board buys often precede 10-15% rallies.",
            "execs": [
                {"name": "Anthony Noto", "role": "CEO", "win_rate": "82%", "avg_return": "+14.2%", "summary": "Highly accurate cluster buyer. Usually initiates large block buys ahead of positive earnings surprises."},
                {"name": "Harvey Schwartz", "role": "Director", "win_rate": "65%", "avg_return": "+8.1%", "summary": "Follows the CEO's lead. Steady buyer during macroeconomic dips."}
            ]
        },
        {
            "ticker": "PLTR", "score": 7.2, "size": 2, "move": -2.1, "price": 21.30, 
            "rsi": 68, "trend": "🟡 Flat", "sector_perf": "-0.5%",
            "analysis": "Strategic accumulation. Executives buying the dip after a minor pullback, likely front-running new government contract announcements.",
            "execs": [
                {"name": "Alex Karp", "role": "CEO", "win_rate": "60%", "avg_return": "+9.0%", "summary": "Rare buyer. When he buys the open market, it typically signals a hard floor in the stock price."},
            ]
        }
    ]
    return [r for r in results if r["size"] >= min_size]


# --- USER INTERFACE ---
st.markdown("### 🏛️ Insider Matrix Pro")
min_cluster = st.slider("Minimum Executives in Cluster", 1, 5, 2)

if st.button("Scan Live Streams", use_container_width=True):
    items = run_math_engine(min_cluster)
    
    for item in items:
        badge = "🟢" if item['score'] >= 7.0 else "🟠"
        
        with st.container(border=True):
            st.markdown(f"### {item['ticker']} {badge} Rank: {item['score']}/10")
            
            # Row 1: Core Metrics
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Live Price", f"${item['price']:.2f}")
            c2.metric("Gap Move", f"{item['move']:.1f}%")
            c3.metric("RSI (Momentum)", item['rsi'])
            c4.metric("Sector Trend", item['sector_perf'])
            
            # Safety Warning based on RSI (Over 70 is overbought, under 30 is oversold)
            if item['rsi'] > 65:
                st.warning("⚠️ **Technical Warning:** Stock is currently running hot (RSI high). Buying right now carries higher risk of a pullback.")
            
            # Row 2: Position Sizing output
            shares_to_buy = calculate_shares(item['price'])
            total_investment = shares_to_buy * item['price']
            st.success(f"**Trade Blueprint:** Buy **{shares_to_buy} shares** (${total_investment:.2f} total). If your {stop_loss_pct}% stop-loss hits, you only lose your max risk of ${max_risk_amount:.2f}.")
            
            st.info(f"**Cluster Analysis:** {item['analysis']}")
            
            # Row 3: Live Chart Integration
            with st.expander(f"📈 View 30-Day Live Chart for {item['ticker']}"):
                try:
                    # Pulls real live chart data from Yahoo Finance
                    hist = yf.download(item['ticker'], period="1mo", interval="1d", progress=False)
                    st.line_chart(hist['Close'])
                except:
                    st.error("Chart data unavailable right now.")
                    
            # Row 4: Executive History
            st.markdown(f"**👥 Cluster: {item['size']} Executives** *(Click for history)*")
            for exec_data in item['execs']:
                with st.expander(f"{exec_data['name']} ({exec_data['role']})"):
                    st.markdown(f"**Profile:** {exec_data['summary']}")
                    st.markdown(f"- **2-Year Win Rate:** {exec_data['win_rate']}")
                    st.markdown(f"- **Avg Cluster Return:** {exec_data['avg_return']}")