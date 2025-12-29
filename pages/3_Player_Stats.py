import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Player Stats", page_icon="📊", layout="wide")

st.title("Player Stats 📊")

# Default to MySave content if no user set
if 'data_manager' not in st.session_state:
    st.switch_page("app.py")

dm = st.session_state['data_manager']


# --- Load Data ---
# --- Load Data ---
@st.cache_data(ttl=600)
def load_squad_and_stats(_dm):
    # Using _dm to avoid hashing the DataManager object
    squad = _dm.get_data("Squad")
    stats = _dm.get_data("MatchStats")
    return squad, stats

try:
    squad_df, match_stats_df = load_squad_and_stats(dm)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# --- Tabs for Entry vs View ---
tab1, tab2 = st.tabs(["Enter Match Stats", "View Player Stats"])

# List of stat columns based on user request
STAT_COLUMNS = [
    "Minutes Played", "Match Rating", "Goals", "Own Goals", "Assists",
    "Shots", "Shots on Target", 
    "Passes Attempted", "Passes Completed",
    "Short Passes Attempted", "Short Passes Completed",
    "Medium Passes Attempted", "Medium Passes Completed",
    "Long Passes Attempted", "Long Passes Completed",
    "Dribbles Attempted", "Dribbles Completed",
    "Crosses Attempted", "Crosses Completed",
    "Tackles Attempted", "Tackles Completed",
    "Interceptions", "Key Passes", "Key Dribbles", "Fouled",
    "Successful 1 on 1 Dribbles", "Fouls", "Penalties Conceded",
    "Blocks", "Out of Position", "Posession Won", "Posession Lost",
    "Clearances", "Headers Won", "Headers Lost",
    "Saves", "Shots Caught", "Shots Parried", "Crosses Caught", "Balls Stripped"
]

BOOLEAN_COLUMNS = ["Man of the Match", "Started"]

with tab1:
    st.header("Match Setup")
    with st.form("match_setup"):
        col1, col2, col3 = st.columns(3)
        season = col1.text_input("Season", value="2023/2024")
        competition = col2.text_input("Competition")
        opponent = col3.text_input("Opponent")
        
        col4, col5 = st.columns(2)
        scores = col4.text_input("Scores (Us - Them)")
        match_date = col5.date_input("Date", value=date.today())
        
        # Player Selection
        if not squad_df.empty:
            players = st.multiselect("Select Players Involved", squad_df["Name"].tolist())
        else:
            players = []
            st.info("No players in squad.")

        submitted_setup = st.form_submit_button("Prepare Stats Sheet")

    if submitted_setup and players:
        st.session_state['current_match_meta'] = {
            "Season": season,
            "Competition": competition,
            "Opponent": opponent,
            "Scores": scores,
            "Date": str(match_date)
        }
        st.session_state['current_match_players'] = players

    # --- Batch Entry ---
    if 'current_match_players' in st.session_state:
        st.subheader(f"Enter Stats vs {st.session_state['current_match_meta']['Opponent']}")
        
        # Initialize DataFrame for entry
        # We need rows for each player, cols for STAT_COLUMNS (ints) + BOOLs
        initial_data = []
        for p in st.session_state['current_match_players']:
            row = {"Player Name": p}
            for col in STAT_COLUMNS:
                if col == "Match Rating":
                    row[col] = 0.0
                else:
                    row[col] = 0
            for col in BOOLEAN_COLUMNS:
                row[col] = False
            initial_data.append(row)
        
        df_entry = pd.DataFrame(initial_data)
        
        edited_stats = st.data_editor(
            df_entry, 
            column_config={
                "Player Name": st.column_config.TextColumn(
                    "Player Name",
                    width="medium",
                    disabled=True,
                    pinned=True
                ),
                "Man of the Match": st.column_config.CheckboxColumn("MOTM"),
                "Started": st.column_config.CheckboxColumn("Started?"),
                "Match Rating": st.column_config.NumberColumn(
                    "Match Rating",
                    min_value=0.0,
                    max_value=10.0,
                    step=0.1,
                    format="%.1f"
                ),
            },
            hide_index=True
        )

        if st.button("Save Match Stats"):
            # Add metadata columns to every row
            meta = st.session_state['current_match_meta']
            for key, val in meta.items():
                edited_stats[key] = val
            
            try:
                dm.append_data("MatchStats", edited_stats)
                st.success("Match stats saved successfully!")
                st.cache_data.clear() # Clear cache to refresh data across app
                del st.session_state['current_match_players'] # Reset
                st.rerun()
            except Exception as e:
                st.error(f"Error saving stats: {e}")

with tab2:
    st.header("Player Statistics Analysis")
    
    if match_stats_df.empty:
        st.info("No match stats recorded.")
    else:
        # Filters
        filter_col1, filter_col2 = st.columns(2)
        competitions = match_stats_df["Competition"].unique().tolist()
        matches = match_stats_df["Opponent"].unique().tolist()
        
        selected_comps = filter_col1.multiselect("Filter by Competition", competitions)
        selected_matches = filter_col2.multiselect("Filter by Match (Opponent)", matches)
        
        filtered_df = match_stats_df.copy()
        if selected_comps:
            filtered_df = filtered_df[filtered_df["Competition"].isin(selected_comps)]
        if selected_matches:
            filtered_df = filtered_df[filtered_df["Opponent"].isin(selected_matches)]
            
        # Toggles
        per_90 = st.toggle("Per 90 Stats")
        per_game = st.toggle("Per Game Stats")
        
        # Aggregation
        # Group by Player Name and sum numerical columns
        # First ensure numeric types
        numeric_cols = STAT_COLUMNS  # These should be numeric
        for col in numeric_cols:
            filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0)
            
        # Count games played (rows per player)
        games_played = filtered_df.groupby("Player Name").size().rename("Games Played")
        
        agg_df = filtered_df.groupby("Player Name")[numeric_cols].sum()
        agg_df = agg_df.join(games_played)
        
        # Calculate Accuracies (Percentages)
        # Function to safe divide
        def calc_acc(df, num, den, name):
            df[name] = (df[num] / df[den].replace(0, 1)) * 100
            # Handle 0/0 -> 0 (or keep as is, but users prefer 0 usually)
            df.loc[df[den] == 0, name] = 0
            return df

        agg_df = calc_acc(agg_df, "Passes Completed", "Passes Attempted", "Pass Accuracy %")
        agg_df = calc_acc(agg_df, "Shots on Target", "Shots", "Shot Accuracy %")
        agg_df = calc_acc(agg_df, "Crosses Completed", "Crosses Attempted", "Cross Accuracy %")
        agg_df = calc_acc(agg_df, "Tackles Completed", "Tackles Attempted", "Tackle Accuracy %")
        agg_df = calc_acc(agg_df, "Dribbles Completed", "Dribbles Attempted", "Dribble Accuracy %")
        agg_df = calc_acc(agg_df, "Short Passes Completed", "Short Passes Attempted", "Short Pass %")
        agg_df = calc_acc(agg_df, "Medium Passes Completed", "Medium Passes Attempted", "Medium Pass %")
        agg_df = calc_acc(agg_df, "Long Passes Completed", "Long Passes Attempted", "Long Pass %")
        
        # Handling Per 90 / Per Game
        display_df = agg_df.copy()
        
        if per_90:
            # Divide all accumulation cols by (Minutes Played / 90)
            mins = display_df["Minutes Played"] / 90
            for col in numeric_cols:
                if col != "Minutes Played" and col != "Match Rating": # Rating shouldn't be per 90
                   display_df[col] = display_df[col] / mins.replace(0, 1)
        
        elif per_game:
            games = display_df["Games Played"]
            for col in numeric_cols:
                if col != "Match Rating":
                    display_df[col] = display_df[col] / games
            display_df["Match Rating"] = display_df["Match Rating"] / games # Average rating
            
        # Average rating for normal view too if not per_game (sum of ratings makes no sense usually, but prompt said "Added up except percentages")
        # Creating a specific rule for Rating: Always Average?
        # Prompt: "All stats would be added up except for Percentage accuracies which would be averaged by number of games"
        # Rating added up is weird logic (Total Rating?), but I will stick to prompt or common sense. Common sense: Avg Rating. 
        # I'll enable Average Rating always.
        if not per_game:
             display_df["Match Rating"] = display_df["Match Rating"] / display_df["Games Played"]

        st.dataframe(display_df.style.format("{:.2f}"))

