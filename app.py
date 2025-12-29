import streamlit as st
import os
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
if 'data_manager' in st.session_state and not hasattr(st.session_state['data_manager'], 'list_saves'):
     st.session_state['data_manager'] = DataManager()
if 'credentials' not in st.session_state:
    st.session_state['credentials'] = None

st.title("Welcome to Retro FIFA Stats ⚽")

# Default Session Setup
# --- Save Management Logic ---
dm = st.session_state['data_manager']
available_saves = dm.list_saves()
if not available_saves:
    # First time run?
    DEFAULT_USER = "MySave"
else:
    DEFAULT_USER = available_saves[0] 

# Session State for Current Save
if 'current_save' not in st.session_state:
    st.session_state['current_save'] = DEFAULT_USER
    
# Sync DataManager
dm.set_user(st.session_state['current_save'])

# --- Sidebar ---
with st.sidebar:
    st.header("Save Management")
    
    # Save Selector
    if available_saves:
        selected_save = st.selectbox(
            "Active Save", 
            available_saves, 
            index=available_saves.index(st.session_state['current_save']) if st.session_state['current_save'] in available_saves else 0
        )
        if selected_save != st.session_state['current_save']:
            st.session_state['current_save'] = selected_save
            dm.set_user(selected_save)
            st.rerun()
    else:
        st.info("No saves found. Create one!")

    st.markdown(f"**Current Save:** {st.session_state['current_save']}")
    st.divider()

# Ensure Data Manager is ready with current save
if not dm.user_email:
    dm.set_user(st.session_state['current_save'])

# Ensure the Excel file exists on startup (for the selected save)
try:
    dm.load_or_create_spreadsheet()
except Exception as e:
    st.error(f"Error initializing data file: {e}")

# Introduction
st.markdown("""
### Welcome to Retro FIFA Stats Tracker
Manage your squad, transfers, and match statistics.  
**Use the sidebar to switch between saves.**
""")

# Data Management Tabs
excel_path = dm.get_excel_path()
dm_tab1, dm_tab2, dm_tab3, dm_tab4 = st.tabs(["🆕 Create Save", "🔗 Combine Saves", "📤 Restore (Upload)", "📥 Backup (Download)"])

import time

# Tab 1: Create New
with dm_tab1:
    st.subheader("Create a New Save")
    st.markdown("Start a fresh journey with a new Team or Manager.")
    
    new_save_name = st.text_input("New Save Name (e.g. 'Arsenal 2004', 'Mourinho')", placeholder="Type name here...")
    
    if st.button("Create Save", type="primary", disabled=not new_save_name):
        safe_name = new_save_name.strip()
        if safe_name in available_saves:
            st.error("A save with this name already exists!")
        elif not safe_name:
             st.error("Please enter a valid name.")
        else:
            try:
                # Switch to new user temporary to create file
                st.session_state['current_save'] = safe_name
                dm.set_user(safe_name)
                dm.load_or_create_spreadsheet()
                st.success(f"Save '{safe_name}' created successfully! Switching...")
                time.sleep(1.0)
                st.rerun()
            except Exception as e:
                st.error(f"Error creating save: {e}")

# Tab 2: Combine Saves
with dm_tab2:
    st.subheader("Combine Saves")
    st.markdown("Merge multiple saves into a new unified save file (e.g. combine 'Season 1' and 'Season 2').")
    
    sources = st.multiselect("Select Saves to Combine", available_saves)
    merged_name = st.text_input("Name for the Merged Save", placeholder="e.g. 'Career Full'")
    
    if st.button("Combine & Create", type="primary", disabled=not (sources and merged_name)):
        success, msg = dm.combine_saves(sources, merged_name)
        if success:
            st.success(msg)
            st.balloons()
            time.sleep(1.5)
            st.rerun() # To refresh the save list
        else:
            st.error(msg)

# Tab 3: Upload (Restore)

with dm_tab3:
    st.subheader("Restore Data")
    st.markdown(f"Upload a previously backed up `.xlsx` file to **overwrite** your current save: **{st.session_state['current_save']}**.")
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

# Tab 4: Download
with dm_tab4:
    st.subheader("Backup Data")
    st.markdown(f"Download a backup of: **{st.session_state['current_save']}**")
    if os.path.exists(excel_path):
        with open(excel_path, "rb") as f:
            st.download_button(
                label=f"Download {st.session_state['current_save']} Backup 📥",
                data=f,
                file_name=f"{st.session_state['current_save']}_Stats_Backup.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Click to download your current data as an Excel file."
            )
    else:
        st.warning("No file found for this save.")

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
**Discord:** mrbubune   
**Version:** 2.0.0
""")

