import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. CONFIG ---
api_key = st.secrets.get("FMP_API_KEY")

# --- 2. DATA ENGINE ---
@st.cache_data(ttl=3600)
def fetch_insider_data():
    # THIS IS THE CURRENT STABLE ENDPOINT
    url = f"https://financialmodelingprep.com/stable/insider-trading/latest?page=0&limit=100&apikey={api_key}"
    
    try:
        response = requests.get(url)
        # Return success with data, or error with text for debugging
        if response.status_code == 200:
            return {"status": 200, "data": response.json()}
        else:
            return {"status": response.status_code, "text": response.text}
    except Exception as e:
        return {"status": "Error", "text": str(e)}

# --- 3. UI ---
st.title("🏛️ Insider Matrix Live")

if not api_key:
    st.error("API Key missing in Secrets. Add it to App Settings > Secrets.")
    st.stop()

result = fetch_insider_data()

# Logic to handle results
if result["status"] == 200:
    st.success("Data Feed Active")
    df = pd.DataFrame(result["data"])
    
    # Simple Cluster View
    st.subheader("Insider Clusters")
    clusters = df.groupby('symbol').agg(
        count=('reportingName', 'nunique'),
        insiders=('reportingName', lambda x: ', '.join(x.unique()))
    ).reset_index()
    
    st.dataframe(clusters.sort_values(by='count', ascending=False), use_container_width=True)
else:
    st.error(f"Connection Failed (Status: {result['status']})")
    st.warning("The API returned this message. Copy this to your FMP dashboard support to resolve:")
    st.code(result["text"])