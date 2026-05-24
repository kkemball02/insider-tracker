import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# --- DATA: HISTORICAL CLUSTERS ---
# This dictionary stores your "lessons learned"
history = [
    {
        "ticker": "SOFI", "date": "2026-05-10", "entry_price": 7.10, "exit_price": 7.42, 
        "risk_pct": 1.0, "result": "Good", "analysis": "Cluster bought at support.",
        "execs": "Anthony Noto, Harvey Schwartz"
    }
]

# --- UI: TABS ---
tab1, tab2 = st.tabs(["Live Scanner", "Trade History & Learning"])

with tab2:
    st.markdown("### 📚 Trade Post-Mortem")
    for trade in history:
        with st.expander(f"{trade['ticker']} - {trade['date']} ({trade['result']})"):
            col1, col2 = st.columns(2)
            col1.write(f"**Analysis:** {trade['analysis']}")
            col2.write(f"**Execs:** {trade['execs']}")
            st.write(f"**Risk Settings Used:** {trade['risk_pct']}% Risk | Entry: ${trade['entry_price']}")
            
            # Plot Chart
            df = yf.download(trade['ticker'], period="3mo", progress=False)
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.add_trace(go.Scatter(x=[trade['date']], y=[trade['entry_price']], mode='markers', name='Your Entry', marker=dict(size=12, color='green')))
            st.plotly_chart(fig, use_container_width=True)

with tab1:
    st.markdown("### 🏛️ Live Scanner")
    # ... (Keep your existing scanner code here)