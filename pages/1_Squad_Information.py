import streamlit as st
import pandas as pd
from data_manager import DataManager

st.set_page_config(page_title="Squad Information", page_icon="📝", layout="wide")

st.title("Squad Information 📝")

# Default to MySave content if no user set (though app.py sets it)
if 'data_manager' not in st.session_state:
    st.switch_page("app.py") # Redirect to home to init

dm = st.session_state['data_manager']



# --- Load Data ---
# --- Load Data ---
@st.cache_data(ttl=600)
def load_squad_data(_dm):
    return _dm.get_data("Squad")

try:
    squad_df = load_squad_data(dm)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- Add Player Form ---
with st.expander("Add New Player"):
    with st.form("add_player_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            season = st.text_input("Season", value="2023/2024")
            name = st.text_input("Name")
            age = st.number_input("Age", min_value=15, max_value=50, step=1)
            kit_number = st.number_input("Kit Number", min_value=1, max_value=99, step=1)
            nationality = st.text_input("Nationality")
            
        with col2:
            pos1 = st.selectbox("Position 1", ["GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "ST", "CF"])
            pos2 = st.selectbox("Position 2 (Optional)", ["Not Set", "GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "ST", "CF"])
            pos3 = st.selectbox("Position 3 (Optional)", ["Not Set", "GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "ST", "CF"])
            pos4 = st.selectbox("Position 4 (Optional)", ["Not Set", "GK", "CB", "LB", "RB", "CDM", "CM", "CAM", "LM", "RM", "LW", "RW", "ST", "CF"])
            strong_foot = st.selectbox("Strong Foot", ["Right", "Left", "Both"])

        with col3:
            height = st.number_input("Height (cm)", min_value=150, max_value=220)
            weight = st.number_input("Weight (kg)", min_value=50, max_value=120)
            transfer_value = st.number_input("Transfer Value ($)", min_value=0)
            wage = st.number_input("Wage ($)", min_value=0)
            contract_len = st.number_input("Contract Length (Years)", min_value=1, max_value=10)
        
        col4, col5, col6 = st.columns(3)
        with col4:
            role = st.selectbox("Role", ["Crucial", "Important", "Rotation", "Sporadic", "Prospect"])
        with col5:
             overall_start = st.number_input("Overall (Start)", min_value=1, max_value=99)
        with col6:
             overall_end = st.number_input("Overall (End)", min_value=1, max_value=99)

        submitted = st.form_submit_button("Add Player")
        
        if submitted:
            if not name:
                st.error("Name is required.")
            else:
                new_player = {
                    "Season": season, "Name": name, "Age": age, "Kit Number": kit_number,
                    "Position 1": pos1, "Position 2": pos2, "Position 3": pos3, "Position 4": pos4,
                    "Nationality": nationality, "Height": height, "Weight": weight,
                    "Transfer Value": transfer_value, "Wage": wage, "Contract Length": contract_len,
                    "Role": role, "Strong Foot": strong_foot,
                    "Overall Start": overall_start, "Overall End": overall_end
                }
                new_df = pd.DataFrame([new_player])
                try:
                    dm.append_data("Squad", new_df)
                    st.success(f"Player {name} added!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving player: {e}")

# --- Edit Squad ---
st.subheader("Current Squad")
st.write("Edit values directly in the table below.")

if not squad_df.empty:
    edited_df = st.data_editor(squad_df, num_rows="dynamic", width='stretch')
    
    if st.button("Save Changes"):
        try:
            dm.write_data("Squad", edited_df)
            st.success("Squad updated successfully!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error saving changes: {e}")
else:
    st.info("No players found. Add a player above.")

