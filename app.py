import streamlit as st
import pandas as pd
import numpy as np

# 1. SETUP DATA
if 'cluster_db' not in st.session_state:
    st.session_state.cluster_db = pd.DataFrame({
        "ticker": ["SOFI", "NVDA", "TSLA"],
        "members": ["Noto, Schwartz", "Pelosi", "Noto, Pelosi, McCarthy"],
        "result": ["Good", "Bad", "Good"],
        "days_to_success": [14, 0, 22],
        "is_cluster": [True, False, True] # True if > 1 member
    })

# 2. ANALYTICS ENGINE
def get_stats(df):
    # Success Rate: % of trades marked 'Good'
    success = (df[df['result'] == 'Good'].shape[0] / df.shape[0]) * 100
    avg_time = df['days_to_success'].mean()
    return success, avg_time

# 3. UI
st.title("🏛️ Cluster Alpha Tracker")

# Sidebar Filters
member_filter = st.sidebar.multiselect("Filter by Member", ["Noto", "Schwartz", "Pelosi", "McCarthy"])
df = st.session_state.cluster_db

# Filter logic
if member_filter:
    df = df[df['members'].apply(lambda x: any(m in x for m in member_filter))]

# 4. DASHBOARD METRICS
col1, col2 = st.columns(2)
cluster_stats = get_stats(df[df['is_cluster'] == True])
solo_stats = get_stats(df[df['is_cluster'] == False])

col1.metric("Cluster Success Rate", f"{cluster_stats[0]:.1f}%", f"Avg {cluster_stats[1]:.1f} days")
col2.metric("Solo Success Rate", f"{solo_stats[0]:.1f}%", f"Avg {solo_stats[1]:.1f} days")

# 5. DATA EDITOR
st.subheader("Raw Cluster Data")
st.session_state.cluster_db = st.data_editor(st.session_state.cluster_db, num_rows="dynamic")