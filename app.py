import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. INITIALIZE DATABASE ---
if 'cluster_db' not in st.session_state:
    st.session_state.cluster_db = pd.DataFrame({
        "ticker": ["SOFI"],
        "member": ["Anthony Noto"],
        "score": [8.5],
        "move": [4.5],
        "price": [7.42],
        "analysis": ["High-density buying across 3 core executives."],
        "date": [datetime.now().strftime("%Y-%m-%d")]
    })

# --- 2. UI: SCANNER (THE MATRIX) ---
st.markdown("### 🏛️ Insider Matrix Live")
min_cluster = st.slider("Minimum Executives in Cluster", min_value=1, max_value=5, value=2)

# Logic to group and score based on your input
df = st.session_state.cluster_db
# This calculates the cluster size dynamically
clusters = df.groupby('ticker').agg(
    size=('member', 'count'), 
    score=('score', 'mean'),
    move=('move', 'mean'),
    price=('price', 'mean'),
    analysis=('analysis', 'first')
).reset_index()

filtered_clusters = clusters[clusters['size'] >= min_cluster]

if st.button("Scan Live Streams", use_container_width=True):
    if filtered_clusters.empty:
        st.warning("No clusters found matching your criteria.")
    
    for _, item in filtered_clusters.iterrows():
        badge = "🟢" if item['score'] >= 7.0 else "🟠"
        
        with st.container(border=True):
            st.markdown(f"### {item['ticker']} {badge} Rank: {item['score']}/10")
            
            col1, col2 = st.columns(2)
            col1.metric("Live Price", f"${item['price']:.2f}")
            col2.metric("Gap Move", f"{item['move']:.1f}%")
            
            st.info(f"**Cluster Analysis:** {item['analysis']}")
            st.markdown(f"**👥 Cluster Size:** {int(item['size'])} Executives")

# --- 3. UI: DATA MANAGEMENT ---
with st.expander("➕ Add Trade or View History"):
    with st.form("add_trade"):
        col_a, col_b = st.columns(2)
        ticker = col_a.text_input("Ticker").upper()
        member = col_b.text_input("Executive/Member")
        score = st.slider("Assign Confidence Score", 1.0, 10.0, 5.0)
        analysis = st.text_area("Analysis")
        if st.form_submit_button("Submit"):
            new_row = pd.DataFrame({"ticker": [ticker], "member": [member], "score": [score], "move": [0.0], "price": [0.0], "analysis": [analysis], "date": [datetime.now().strftime("%Y-%m-%d")]})
            st.session_state.cluster_db = pd.concat([st.session_state.cluster_db, new_row], ignore_index=True)
            st.rerun()
            
    st.dataframe(st.session_state.cluster_db)