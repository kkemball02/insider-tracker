import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Set page layout
st.set_page_config(page_title="Insider Matrix", layout="centered")

# --- DATA ENGINE ---
def run_math_engine(min_size):
    # Simulated database with the new metrics and historical data
    results = [
        {
            "ticker": "SOFI", 
            "score": 8.5, 
            "size": 3, 
            "move": 4.5, 
            "price": 7.42, 
            "analysis": "High-density buying across 3 core executives during a slight dip suggests confidence in upcoming Q3 guidance. Historically, coordinated SOFI board buys precede 10-15% rallies.",
            "execs": [
                {"name": "Anthony Noto", "role": "CEO", "win_rate": "82%", "avg_return": "+14.2%", "summary": "Highly accurate cluster buyer. Usually initiates large block buys ahead of positive earnings surprises."},
                {"name": "Harvey Schwartz", "role": "Director", "win_rate": "65%", "avg_return": "+8.1%", "summary": "Follows the CEO's lead. Steady buyer during macroeconomic dips."},
                {"name": "Chad Borton", "role": "Exec VP", "win_rate": "70%", "avg_return": "+11.5%", "summary": "Aggressive purchaser when stock dips below the 50-day moving average."}
            ]
        },
        {
            "ticker": "PLTR", 
            "score": 7.2, 
            "size": 2, 
            "move": -2.1, 
            "price": 21.30, 
            "analysis": "Strategic accumulation. Executives buying the dip after a minor pullback, likely front-running new government contract announcements.",
            "execs": [
                {"name": "Alex Karp", "role": "CEO", "win_rate": "60%", "avg_return": "+9.0%", "summary": "Rare buyer. When he buys the open market, it typically signals a hard floor in the stock price."},
                {"name": "Shyam Sankar", "role": "COO", "win_rate": "75%", "avg_return": "+12.4%", "summary": "High-frequency trader for his own stock. Very good at timing local bottoms."}
            ]
        }
    ]
    # Filter based on the slider
    return [r for r in results if r["size"] >= min_size]


# --- USER INTERFACE ---
st.markdown("### 🏛️ Insider Matrix Live")

# The new options slider
min_cluster = st.slider("Minimum Executives in Cluster", min_value=1, max_value=5, value=2)

if st.button("Scan Live Streams", use_container_width=True):
    items = run_math_engine(min_cluster)
    
    if not items:
        st.warning("No clusters found matching your criteria right now.")
        
    for item in items:
        badge = "🟢" if item['score'] >= 7.0 else "🟠"
        
        # Main Card using native UI for perfect text colors
        with st.container(border=True):
            st.markdown(f"### {item['ticker']} {badge} Rank: {item['score']}/10")
            
            # Price and Gap in clean metric boxes
            col1, col2 = st.columns(2)
            col1.metric("Live Price", f"${item['price']:.2f}")
            col2.metric("Gap Move", f"{item['move']:.1f}%")
            
            # The AI Summary Analysis Box
            st.info(f"**Cluster Analysis:** {item['analysis']}")
            
            st.markdown(f"**👥 Cluster: {item['size']} Executives** *(Click names for history)*")
            
            # Clickable dropdowns for each executive
            for exec_data in item['execs']:
                with st.expander(f"{exec_data['name']} ({exec_data['role']})"):
                    st.markdown(f"**Profile:** {exec_data['summary']}")
                    st.markdown(f"- **2-Year Win Rate:** {exec_data['win_rate']}")
                    st.markdown(f"- **Avg Cluster Return:** {exec_data['avg_return']}")