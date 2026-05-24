import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_insider_trades(api_key):
    # FIXED: Switched to the correct /stable/ endpoint
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "text": response.text}
    except Exception as e:
        return {"error": str(e)}

# --- 2. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")

# --- 3. UI ---
st.markdown("### 🏛️ Insider Matrix Live")
data = fetch_insider_trades(api_key)

# Tab structure
tab1, tab2 = st.tabs(["🏛️ Insider Matrix", "🛠️ Data Feed Debug"])

with tab2:
    if isinstance(data, dict) and "error" in data:
        st.error(f"Error: {data['error']}")
        st.code(data['text'])
    else:
        st.write("Data Feed Connected Successfully.")
        st.json(data[:5]) # Show first 5 items to verify

with tab1:
    if isinstance(data, list) and len(data) > 0:
        df = pd.DataFrame(data)
        
        # Display Summary
        st.success("Insider Data Feed Active")
        
        # Simple Clustering: Group by symbol and count insiders
        clusters = df.groupby('symbol').agg(
            count=('reportingName', 'nunique'),
            insiders=('reportingName', lambda x: ', '.join(x.unique()))
        ).reset_index()
        
        # Show top clusters
        st.dataframe(clusters.sort_values(by='count', ascending=False), use_container_width=True)
    elif isinstance(data, dict):
        st.warning("Data load failed. Check the 'Data Feed Debug' tab for the error code.")
    else:
        st.warning("No data found.")