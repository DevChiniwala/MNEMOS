import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# Configuration
API_URL = "http://localhost:8000/v1"

st.set_page_config(page_title="MNEMOS Console", layout="wide", page_icon="🧠")

st.title("🧠 MNEMOS Observability Console")
st.markdown("Monitor and debug your AI agent's temporal memory.")

def fetch_active_memories():
    try:
        res = requests.get(f"{API_URL}/memories")
        if res.status_code == 200:
            return res.json().get("memories", [])
        else:
            st.error(f"Failed to fetch memories: {res.status_code}")
            return []
    except Exception as e:
        st.error(f"API Connection Error: Ensure MNEMOS server is running on port 8000.\n{e}")
        return []

memories = fetch_active_memories()

if not memories:
    st.info("No active memories found or server not reachable.")
else:
    df = pd.DataFrame(memories)
    
    # 1. High-level metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Memories", len(df))
    
    # Tier distribution
    if "tier" in df.columns:
        tiers = df['tier'].value_counts()
        col2.metric("Short Tier", tiers.get("short", 0))
        col3.metric("Mid Tier", tiers.get("mid", 0))
        col4.metric("Long Tier", tiers.get("long", 0))

    st.divider()
    
    # 2. Timeline Visualization
    st.subheader("Memory Timeline")
    st.markdown("Visualizing when memories were created and their temporal validity.")
    
    # Convert timestamps
    if "t_created" in df.columns:
        df["t_created_dt"] = pd.to_datetime(df["t_created"])
        
        # Simple scatter timeline
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.scatter(df["t_created_dt"], [1]*len(df), alpha=0.6, color="#4F46E5")
        ax.set_yticks([])
        ax.set_xlabel("Creation Time")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        st.pyplot(fig)

    st.divider()

    # 3. Data Explorer
    st.subheader("Memory Explorer")
    
    search = st.text_input("Filter content:")
    display_df = df
    if search:
        display_df = display_df[display_df['content'].str.contains(search, case=False, na=False)]
        
    st.dataframe(
        display_df[["id", "content", "tier", "t_created"]].sort_values(by="t_created", ascending=False),
        use_container_width=True
    )
    
    st.subheader("Inspect Memory Details")
    memory_id = st.selectbox("Select Memory ID", display_df["id"].tolist())
    
    if memory_id:
        try:
            detail_res = requests.get(f"{API_URL}/memories/{memory_id}")
            if detail_res.status_code == 200:
                details = detail_res.json()
                st.json(details)
            else:
                st.warning("Could not fetch memory details.")
        except Exception:
            pass
