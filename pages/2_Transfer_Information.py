import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Transfer Information", page_icon="💸", layout="wide")

st.title("Transfer Information 💸")

# Default to MySave content if no user set
if 'data_manager' not in st.session_state:
    st.switch_page("app.py")

dm = st.session_state['data_manager']


# --- Load Data ---
# --- Load Data ---
@st.cache_data(ttl=600)
def load_transfer_data(_dm):
    return _dm.get_data("Transfers"), _dm.get_data("Squad")

try:
    transfers_df, squad_df = load_transfer_data(dm)
except Exception as e:
    st.error(f"Error loading sheets: {e}")
    st.stop()

# --- Add Transfer Form ---
with st.expander("Add New Transfer"):
    with st.form("add_transfer_form"):
        col1, col2 = st.columns(2)
        with col1:
            season = st.text_input("Season", value="2023/2024")
            # Try to populate names from squad if available, otherwise text
            player_names = squad_df["Name"].tolist() if not squad_df.empty else []
            name_input_method = st.radio("Player Input Method", ["Select Existing", "Enter New Name"], horizontal=True)
            
            if name_input_method == "Select Existing" and player_names:
                player_name = st.selectbox("Player Name", player_names)
            else:
                player_name = st.text_input("Player Name")
                
            transfer_date = st.date_input("Transfer Date", value=date.today())

        with col2:
            t_type = st.selectbox("Transfer Type", [
                "Transfer In", "Transfer Out", 
                "Loan In", "Loan Out", 
                "Loan In (Option to Buy)", "Loan Out (Option to Buy)"
            ])
            value = st.text_input("Transfer Value (Money or % split)")

        submitted = st.form_submit_button("Add Transfer")
        if submitted:
            if not player_name:
                st.error("Player Name is required.")
            else:
                new_transfer = {
                    "Season": season,
                    "Player Name": player_name,
                    "Transfer Date": str(transfer_date),
                    "Transfer Type": t_type,
                    "Transfer Value": value
                }
                try:
                    dm.append_data("Transfers", pd.DataFrame([new_transfer]))
                    st.success("Transfer added!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving transfer: {e}")

# --- View Transfers ---
st.subheader("Transfer History")
if not transfers_df.empty:
    st.dataframe(transfers_df, width='stretch')
else:
    st.info("No transfers recorded yet.")

