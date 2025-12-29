import streamlit as st
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from data_manager import DataManager

st.set_page_config(
    page_title="Retro FIFA Stats",
    page_icon="⚽",
    layout="wide"
)

# Initialize Session State
if 'data_manager' not in st.session_state:
    st.session_state['data_manager'] = DataManager()
# Fix for hot-reloading code: Re-init DataManager if it's missing the new method
if 'data_manager' in st.session_state and not hasattr(st.session_state['data_manager'], 'get_excel_path'):
     st.session_state['data_manager'] = DataManager()
if 'credentials' not in st.session_state:
    st.session_state['credentials'] = None

st.title("Welcome to Retro FIFA Stats ⚽")

# Default Session Setup
DEFAULT_USER = "MySave"

# Ensure Data Manager is ready
dm = st.session_state['data_manager']
if not dm.user_email:
    dm.set_user(DEFAULT_USER)
    
# Ensure the Excel file exists on startup
try:
    dm.load_or_create_spreadsheet()
except Exception as e:
    st.error(f"Error initializing data file: {e}")

# Introduction
st.markdown("""
### Welcome to Retro FIFA Stats Tracker
Manage your squad, transfers, and match statistics. Use the tools below to manage your save file (Create, Backup, or Restore).
""")

# Data Management Tabs
excel_path = dm.get_excel_path(DEFAULT_USER)
dm_tab1, dm_tab2, dm_tab3 = st.tabs(["🆕 Create New Save", "📤 Restore (Upload)", "📥 Backup (Download)"])

import time

# Tab 1: Create New
with dm_tab1:
    st.subheader("Start Fresh")
    st.warning("⚠️ **Warning:** This will delete your current session data and create a new empty file. Make sure you have downloaded a backup if needed!")
    
    if st.button("Create New Empty Save", type="primary"):
            try:
                # Delete existing if any
                if os.path.exists(excel_path):
                    os.remove(excel_path)
                # Trigger creation
                dm.load_or_create_spreadsheet()
                st.success("New save file created successfully! reloading...")
                st.cache_data.clear()
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error creating new save: {e}")

# Tab 2: Upload (Restore)
with dm_tab2:
    st.subheader("Restore Data")
    st.markdown("Upload a previously backed up `.xlsx` file to **overwrite** your current session data.")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"], key="restore_uploader")
    
    if uploaded_file:
        if st.button("Confirm Restore (Overwrite Data)", type="primary"):
            try:
                # Save uploaded file to the target path, overwriting existing
                with open(excel_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Data restored successfully! Reloading...")
                st.cache_data.clear()
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Error restoring file: {e}")

# Tab 3: Download
with dm_tab3:
    st.subheader("Backup Data")
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.download_button(
                label="Download Excel Backup 📥",
                data=f,
                file_name="RetroFIFA_Stats_Backup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Click to download your current data as an Excel file."
            )
        st.success("File ready for download.")
    else:
        st.warning("No data file found. Create a new save or upload one.")

st.markdown("---")
st.markdown("""
### Go to pages:
- **Squad Information**: Manage your players.
- **Transfer Information**: Manage transfers.
- **Player Stats**: Record match stats.
- **Team Stats**: View analysis.
- **Stats Dashboard**: Advanced visualizations.
""")

# Contact Info
st.markdown("---")
st.subheader("Contact Information")
st.markdown("""
**Created by:** MrBubune
**Email:** daryl.narh@gmail.com
**Version:** 1.0.0
""")

