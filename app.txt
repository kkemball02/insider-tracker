import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(page_title="Insider Matrix", layout="centered")

def run_math_engine():
    # This simulates the SEC pipeline data
    return [
        {"ticker": "SOFI", "score": 8.5, "size": 3, "move": 4.5, "price": 7.42, "execs": "Anthony Noto, Harvey Schwartz, Chad Borton"}
    ]

st.markdown("### 🏛️ Insider Matrix Live")
if st.button("Scan Live Streams", use_container_width=True):
    items = run_math_engine()
    for item in items:
        badge = "🟢" if item['score'] >= 7.0 else "🟠"
        st.markdown(f"""
        <div style='background: #262730; padding: 15px; border-radius: 10px; border: 1px solid #444;'>
            <h3>{item['ticker']} {badge} Rank: {item['score']}/10</h3>
            <p>Live Price: ${item['price']:.2f} | Gap: {item['move']:.1f}%</p>
            <p style='color: #4da6ff;'>👥 Cluster: {item['size']} Executives</p>
            <small style='color: #aaa;'>{item['execs']}</small>
        </div>
        """, unsafe_allow_html=True)