import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Team Stats", page_icon="🏆", layout="wide")

st.title("Team Stats 🏆")

# Default to MySave content if no user set
if 'data_manager' not in st.session_state:
    st.switch_page("app.py")

dm = st.session_state['data_manager']


# --- Load Data ---
@st.cache_data(ttl=600)
def load_match_stats(_dm):
    return _dm.get_data("MatchStats")

try:
    match_stats_df = load_match_stats(dm)
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

if match_stats_df.empty:
    st.info("No match data available.")
else:
    # Sidebar Filters
    st.sidebar.header("Filters")
    seasons = match_stats_df["Season"].astype(str).unique()
    competitions = match_stats_df["Competition"].unique()
    
    selected_season = st.sidebar.selectbox("Season", seasons)
    selected_comp = st.sidebar.selectbox("Competition", ["All"] + list(competitions))
    
    # Filter Data
    df = match_stats_df[match_stats_df["Season"].astype(str) == selected_season]
    if selected_comp != "All":
        df = df[df["Competition"] == selected_comp]
        
    if df.empty:
        st.warning("No stats for this selection.")
    else:
        # --- Team Performance (W/D/L) ---
        # We need unique matches to calculate W/D/L, but stats are per player.
        # We can drop duplicates by (Season, Competition, Opponent, Date) to get unique matches.
        matches_df = df[["Season", "Competition", "Opponent", "Scores", "Date"]].drop_duplicates()
        
        wins = 0
        draws = 0
        losses = 0
        
        for index, row in matches_df.iterrows():
            score_str = str(row["Scores"])
            # Try to parse "Home - Away" or "Home-Away"
            # Assuming user team is always first number per "Scores" field input assumption
            parts = re.split(r'\D+', score_str) # split by non-digits
            parts = [p for p in parts if p] # filter empty
            
            if len(parts) >= 2:
                try:
                    us = int(parts[0])
                    them = int(parts[1])
                    if us > them:
                        wins += 1
                    elif us == them:
                        draws += 1
                    else:
                        losses += 1
                except:
                    pass # cannot parse
                    
        # Display W/D/L
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Games Played", len(matches_df))
        col2.metric("Wins", wins)
        col3.metric("Draws", draws)
        col4.metric("Losses", losses)
        
        # --- Aggregated Stats ---
        st.subheader("Aggregated Team Stats")
        
        # Identify numeric columns (Stats)
        # We need to exclude metadata and booleans
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        # Filter out obvious metadata if they got detected as numeric
        numeric_cols = [c for c in numeric_cols if c not in ["Season", "Year"]]
        
        # Sum all stats
        team_totals = df[numeric_cols].sum()
        
        # Divide by Games Played for "Per Game" on Team Level? 
        # Requirement: "Show users complete team stats per season (By adding and averaging for all players and all matches)"
        # "Averaging for all players" is ambiguous. Usually Team Stats = Sum of all players. 
        # "Averaging" might mean Per Game.
        # I will show Totals and Per Game Average
        
        st.dataframe(pd.DataFrame({
            "Total": team_totals,
            "Per Match Avg": team_totals / len(matches_df) if len(matches_df) > 0 else 0
        }).style.format("{:.2f}"))

