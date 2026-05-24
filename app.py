import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Insider Matrix", layout="wide")

# --- 1. CONFIG ---
API_KEY = st.secrets.get("FMP_API_KEY")

# --- 2. THE DIAGNOSTIC ENGINE ---
@st.cache_data(ttl=3600)
def fetch_data():
    # This is the specific URL documented for the Free tier "Latest Insider Trading"
    url = f"https://financialmodelingprep.com/api/v3/insider-trading/latest?limit=100&apikey={API_KEY}"
    try:
        response = requests.get(url)
        return {
            "status": response.status_code,
            "data": response.json() if response.status_code == 200 else None,
            "text": response.text # Shows the actual error message
        }
    except Exception as e:
        return {"status": "Error", "text": str(e)}

# --- 3. UI ---
st.title("🏛️ Insider Matrix Debugger")

if not API_KEY:
    st.error("API Key missing in Secrets. Please add it.")
    st.stop()

result = fetch_data()

if result["status"] == 200:
    st.success("Successfully connected to FMP!")
    df = pd.DataFrame(result["data"])
    st.dataframe(df, use_container_width=True)
else:
    st.error(f"Connection Failed (Status: {result['status']})")
    st.code(result["text"]) # This displays the exact error from FMP
    st.info("Copy the error code above and verify it against your FMP Dashboard.")
