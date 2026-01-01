import streamlit as st
import io
import time
from data_manager import DataManager

st.set_page_config(
    page_title="Retro FIFA Stats",
    page_icon="⚽",
    layout="wide"
)

# Initialize Session State
if 'data_manager' not in st.session_state:
    st.session_state['data_manager'] = DataManager()

dm = st.session_state['data_manager']

st.title("Welcome to Retro FIFA Stats ⚽")

st.info("This app runs in your browser. Data is NOT saved to the server. Please DOWNLOAD your save file before closing the tab.")

# --- Sidebar ---
with st.sidebar:
    st.header("Save Management")
    
    # Save Name
    new_name = st.text_input("Save Name", value=dm.current_save_name)
    if new_name != dm.current_save_name:
        dm.current_save_name = new_name
    
    # Download Save
    st.subheader("1. Save Data")
    excel_data = dm.save_to_bytes()
    st.download_button(
        label="Download Save File 📥",
        data=excel_data,
        file_name=f"{dm.current_save_name}_Stats.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Download your current progress to your computer."
    )
    
    st.divider()
    
    # Upload Save
    st.subheader("2. Load Data")
    uploaded_file = st.file_uploader("Upload Save File", type=["xlsx"], label_visibility="collapsed")
    if uploaded_file:
        if st.button("Load Uploaded Save", type="primary"):
            success, msg = dm.load_from_bytes(uploaded_file)
            if success:
                st.success(msg)
                time.sleep(1)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    
    # Reset
    st.subheader("3. Reset")
    if st.button("Start New Save (Clear Data)", type="secondary"):
        st.session_state['data_manager'] = DataManager()
        st.rerun()

# --- Main Content ---
st.markdown("""
### Welcome to Retro FIFA Stats Tracker
Manage your squad, transfers, and match statistics locally in your browser.

**How to use:**
1. **Start New:** The app starts with a fresh empty database.
2. **Work:** Add players, matches, and stats in the pages.
3. **Save:** Click **Download Save File** in the sidebar to keep your progress.
4. **Resume:** Next time, upload that file to continue where you left off.
""")

st.markdown("---")
st.markdown("""
### Go to pages:
- **Squad Information**: Manage your players.
- **Transfer Information**: Manage transfers (Work in Progress).
- **Player Stats**: Record match stats.
- **Team Stats**: View analysis (Work in Progress).
- **Stats Dashboard**: Advanced visualizations.
""")

# Contact Info
st.markdown("---")
st.subheader("Contact Information")
st.markdown("""
**Created by:** MrBubune   
**Discord:** mrbubune   
**Version:** 2.1.0 (Cloud Ready)
""")
