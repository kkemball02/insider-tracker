import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(layout="wide", page_title="Congressional Cluster Tracker")

# --- 1. INITIALIZE DATA ---
if 'cluster_db' not in st.session_state:
    st.session_state.cluster_db = pd.DataFrame({
        "ticker": ["SOFI"],
        "member": ["Noto"],
        "date": ["2026-05-10"],
        "entry_price": [7.10],
        "suggested_buy": [6.90],
        "risk_pct": [1.5],
        "result": ["Good"],
        "analysis": ["Cluster bought at support."]
    })

# --- 2. HELPER FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_chart_data(ticker):
    df = yf.download(ticker, period="3mo", progress=False)
    # Fix for newer yfinance index issues
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

# --- 3. UI LAYOUT ---
st.title("🏛️ Congressional Cluster Tracker")
tab1, tab2 = st.tabs(["🏛️ Live Scanner", "📚 History & Analytics"])

# --- TAB 1: SCANNER ---
with tab1:
    st.markdown("### Add New Trade Data")
    with st.form("add_trade"):
        col_a, col_b = st.columns(2)
        new_ticker = col_a.text_input("Ticker").upper()
        new_member = col_b.text_input("Member Name")
        col_c, col_d = st.columns(2)
        entry = col_c.number_input("Entry Price", value=0.0)
        sug_entry = col_d.number_input("Suggested Entry", value=0.0)
        submit = st.form_submit_button("Log Trade")
        
        if submit and new_ticker:
            new_row = pd.DataFrame({
                "ticker": [new_ticker], "member": [new_member], "date": [datetime.now().strftime("%Y-%m-%d")],
                "entry_price": [entry], "suggested_buy": [sug_entry], "risk_pct": [1.0], 
                "result": ["Pending"], "analysis": ["New entry"]
            })
            st.session_state.cluster_db = pd.concat([st.session_state.cluster_db, new_row], ignore_index=True)

    st.divider()
    
    # Scanner Logic: Identify Clusters (>1 person per ticker)
    st.subheader("Detected Clusters")
    df = st.session_state.cluster_db
    clusters = df.groupby('ticker').agg(members=('member', lambda x: ', '.join(x.unique())), count=('member', 'nunique'))
    active_clusters = clusters[clusters['count'] >= 2] # Set to 2 or 3 depending on your strictness
    
    if not active_clusters.empty:
        st.dataframe(active_clusters)
    else:
        st.info("No clusters detected yet. Need 2+ officials on a ticker.")

# --- TAB 2: HISTORY & ANALYTICS ---
with tab2:
    st.subheader("Edit & Analyze History")
    # Interactive Table
    st.session_state.cluster_db = st.data_editor(st.session_state.cluster_db, num_rows="dynamic")
    
    st.divider()
    
    for _, row in st.session_state.cluster_db.iterrows():
        with st.expander(f"{row['ticker']} - {row['date']} | Result: {row['result']}"):
            col1, col2 = st.columns(2)
            col1.write(f"**Analysis:** {row['analysis']}")
            col2.write(f"**Members:** {row['member']}")
            
            # Chart
            df = get_chart_data(row['ticker'])
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.add_trace(go.Scatter(x=[pd.to_datetime(row['date'])], y=[row['entry_price']], mode='markers', name='Your Entry', marker=dict(size=12, color='green')))
            fig.add_trace(go.Scatter(x=[pd.to_datetime(row['date'])], y=[row['suggested_buy']], mode='markers', name='Suggested Buy', marker=dict(size=12, color='blue', symbol='x')))
            fig.update_layout(template="plotly_dark", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)