import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import numpy as np

st.set_page_config(page_title="Stats Dashboard", page_icon="📈", layout="wide")

st.title("Stats Dashboard 📈")

# --- Authentication Check ---
# Default to MySave content if no user set
if 'data_manager' not in st.session_state:
    st.switch_page("app.py")

# --- Data Loading ---
dm = st.session_state['data_manager']


@st.cache_data(ttl=600)
def load_data(_dm):
    try:
        squad = _dm.get_data("Squad")
        match_stats = _dm.get_data("MatchStats")
        transfers = _dm.get_data("Transfers")
        return squad, match_stats, transfers
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

squad_df, match_stats_df, transfers_df = load_data(dm)

if match_stats_df.empty:
    st.info("No match stats available to analyze.")
    st.stop()

# --- Data Preprocessing ---
# Convert numeric columns
numeric_cols = [
    "Minutes Played", "Match Rating", "Goals", "Own Goals", "Assists",
    "Shots", "Shots on Target", "Passes Attempted", "Passes Completed",
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

for col in numeric_cols:
    if col in match_stats_df.columns:
        match_stats_df[col] = pd.to_numeric(match_stats_df[col], errors='coerce').fillna(0)

# Merge Squad info (Position, Nationality, etc.)
# We need to handle potential duplicates in Squad if same player is in multiple seasons
# We merge on Name and Season
squad_info = squad_df[["Name", "Season", "Position 1", "Position 2", "Position 3", "Position 4", "Nationality", "Age"]]
squad_info = squad_info.rename(columns={"Name": "Player Name"})

# Ensure Season columns match type and clean strings for matching
squad_info["Season"] = squad_info["Season"].astype(str).str.strip()
match_stats_df["Season"] = match_stats_df["Season"].astype(str).str.strip()
squad_info["Player Name"] = squad_info["Player Name"].astype(str).str.strip()
match_stats_df["Player Name"] = match_stats_df["Player Name"].astype(str).str.strip()

# Create normalized keys for merging
squad_info["_merge_name"] = squad_info["Player Name"].str.lower()
squad_info["_merge_season"] = squad_info["Season"].str.lower()
match_stats_df["_merge_name"] = match_stats_df["Player Name"].str.lower()
match_stats_df["_merge_season"] = match_stats_df["Season"].str.lower()

merged_df = pd.merge(match_stats_df, squad_info, left_on=["_merge_name", "_merge_season"], right_on=["_merge_name", "_merge_season"], how="left", suffixes=("", "_squad"))

# Drop helper columns and duplicate columns if any (suffixes handle name/season duplicates but we want to keep original MatchStats name/season usually)
# Actually, since we join on name/season, we should be careful.
# The merge will keep both if headers differ, or use suffixes.
# We want to keep the canonical name from one of them.
# Drop _merge columns
merged_df = merged_df.drop(columns=["_merge_name", "_merge_season"])
# If suffixes created duplicate Name/Season columns, we might need to clean up.
# right_on/left_on keeps the key columns from both if they have different names. Here they are _merge_*.
# But "Player Name" and "Season" exist in both. list(match_stats) and list(squad).
# pandas merge with on=... keeps 1. with left_on/right_on it keeps both?
# We used separate specific columns for keys. The original "Player Name" and "Season" columns are NOT used as keys.
# So "Player Name" from match_stats and "Player Name" from squad will both be present as "Player Name" and "Player Name_squad".
# We should coalesce them or just use match_stats one.
# Let's drop the _squad versions.
if "Player Name_squad" in merged_df.columns:
    merged_df = merged_df.drop(columns=["Player Name_squad"])
if "Season_squad" in merged_df.columns:
    merged_df = merged_df.drop(columns=["Season_squad"])

# Aggregation helper
def aggregate_stats(df, group_cols):
    agg_funcs = {col: 'sum' for col in numeric_cols if col != "Match Rating"}
    agg_funcs["Match Rating"] = 'mean'
    
    # Metadata to preserve (taking first value found in group)
    meta_cols = ["Position 1", "Position 2", "Position 3", "Position 4", "Nationality", "Age", "Season"]
    for mc in meta_cols:
        if mc in df.columns and mc not in group_cols:
            agg_funcs[mc] = 'first'
    
    # Games played
    games = df.groupby(group_cols).size().rename("Games Played")
    
    # Sums
    agg = df.groupby(group_cols).agg(agg_funcs)
    agg = agg.join(games)
    
    # Recalculate Per 90
    agg["90s Played"] = agg["Minutes Played"] / 90
    
    return agg.reset_index()

# Constants
CATEGORY_PRESETS = {
    "Attack": ["Match Rating", "Goals", "Shots", "Shots on Target", "Assists", "Key Passes", "Dribbles Completed", "Crosses Completed", "Fouled", "Penalties Conceded", "Posession Lost"],
    "Midfield": ["Match Rating", "Goals", "Assists", "Passes Completed", "Passes Attempted", "Dribbles Attempted", "Dribbles Completed", "Tackles Completed", "Interceptions", "Posession Won", "Posession Lost", "Key Passes"],
    "Defence": ["Match Rating", "Goals", "Own Goals", "Tackles Completed", "Interceptions", "Clearances", "Headers Won", "Blocks", "Posession Won", "Posession Lost", "Penalties Conceded"],
    "Goalkeeper": ["Match Rating", "Saves", "Shots Caught", "Shots Parried", "Crosses Caught", "Goals Conceded", "Posession Won", "Balls Stripped"], # Note: Goals Conceded distinct from Own Goals? MatchStats has Own Goals but maybe not Goals Conceded column. Using existing columns.
    "Possession": ["Passes Attempted", "Passes Completed", "Dribbles Attempted", "Dribbles Completed", "Key Passes", "Key Dribbles", "Posession Won", "Posession Lost"]
}

# Fix for Goalkeeper: 'Goals Conceded' might not exist in MatchStats based on data_manager.py.
# Using 'Own Goals' or maybe we need to derive it from score? Unclear. I will omit 'Goals Conceded' if not present.
if "Goals Conceded" not in match_stats_df.columns:
    CATEGORY_PRESETS["Goalkeeper"] = [c for c in CATEGORY_PRESETS["Goalkeeper"] if c != "Goals Conceded"]


# --- UI Structure ---
tab1, tab2, tab3 = st.tabs(["Stats Dashboard", "Player Comparison", "Player Scout Report"])

# === TAB 1: STATS DASHBOARD ===
with tab1:
    st.header("Stats Dashboard")
    
    menu = st.radio("View", ["Overall Player Performance", "Multi-Stat Comparison"], horizontal=True)
    
    # Global Filter for this tab
    multi_season = st.toggle("Compare Across Seasons", value=True)
    
    if multi_season:
        df_to_use = merged_df
        # If multiple seasons, grouping by Name + Season? Or just Name to aggregate career?
        # "Allows comparing players across seasons" -> implies we see Player X (2023) vs Player Y (2024) OR Player X (Total).
        # Standard: Group by Player Name + Season to treat them as separate entities for comparison
        group_cols = ["Player Name", "Season"]
    else:
        seasons = sorted(merged_df["Season"].unique())
        if seasons:
            selected_season = st.selectbox("Select Season", seasons, index=len(seasons)-1)
            df_to_use = merged_df[merged_df["Season"] == selected_season]
        else:
            df_to_use = merged_df
        group_cols = ["Player Name"]

    # Aggregate
    agg_data = aggregate_stats(df_to_use, group_cols)
    
    # Aggregate
    agg_data = aggregate_stats(df_to_use, group_cols)
    
    if menu == "Overall Player Performance":
        col1, col2, col3, col4 = st.columns(4)
        
        stat = col1.selectbox("Select Stat", numeric_cols, index=numeric_cols.index("Goals") if "Goals" in numeric_cols else 0)
        top_n = col2.slider("Number of Players", 5, 50, 20)
        lower_is_better = col3.toggle("Lower is Better", value=False)
        show_per_90 = col4.toggle("Per 90", value=False)
        
        # Prepare Data
        plot_df = agg_data.copy()
        y_col = stat
        
        if show_per_90 and stat != "Match Rating":
            plot_df[f"{stat} per 90"] = plot_df[stat] / plot_df["90s Played"].replace(0, 1)
            y_col = f"{stat} per 90"
            
        # Sort
        # If lower_is_better is True (Rank 1 is best), we want smallest values. ascending=True.
        # If lower_is_better is False (Goals 30 is best), we want largest values. ascending=False.
        plot_df = plot_df.sort_values(by=y_col, ascending=lower_is_better).head(top_n)
        
        # Label
        if multi_season:
            plot_df["Label"] = plot_df["Player Name"] + " (" + plot_df["Season"] + ")"
        else:
            plot_df["Label"] = plot_df["Player Name"]
            
        # Chart
        fig = px.bar(
            plot_df, 
            x="Label", 
            y=y_col,
            color="Position 1" if "Position 1" in plot_df.columns else None,
            title=f"Top {top_n} {stat}{' (Per 90)' if show_per_90 else ''}",
            text_auto='.2f'
        )
        # Ensure visual sorting follows value
        fig.update_layout(xaxis={'categoryorder':'total descending' if not lower_is_better else 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Table
        # Table
        cols_to_show = ["Player Name", "Season", "Position 1", "Nationality", "Age", "Minutes Played"]
        if y_col not in cols_to_show:
            cols_to_show.append(y_col)
        st.dataframe(plot_df[cols_to_show].style.format({y_col: "{:.2f}"}))

    elif menu == "Multi-Stat Comparison":
        col1, col2, col3 = st.columns(3)
        stat_x = col1.selectbox("Stat X", numeric_cols, index=numeric_cols.index("Passes Attempted") if "Passes Attempted" in numeric_cols else 0)
        stat_y = col2.selectbox("Stat Y", numeric_cols, index=numeric_cols.index("Passes Completed") if "Passes Completed" in numeric_cols else 1)
        stat_z = col3.selectbox("Stat Z (Optional 3D)", ["None"] + numeric_cols)
        
        extra_col1, extra_col2, extra_col3, extra_col4 = st.columns(4)
        show_trend = extra_col1.toggle("Trendline (OLS)", value=True)
        show_median = extra_col2.toggle("Median Lines", value=True)
        show_per_90_scatter = extra_col3.toggle("Show Per 90", key="scatter_p90")
        
        # Prepare Data
        scatter_df = agg_data.copy()
        x_val = stat_x
        y_val = stat_y
        z_val = None
        
        if show_per_90_scatter:
            if stat_x != "Match Rating":
                scatter_df[f"{stat_x} per 90"] = scatter_df[stat_x] / scatter_df["90s Played"].replace(0, 1)
                x_val = f"{stat_x} per 90"
            if stat_y != "Match Rating":
                scatter_df[f"{stat_y} per 90"] = scatter_df[stat_y] / scatter_df["90s Played"].replace(0, 1)
                y_val = f"{stat_y} per 90"
            if stat_z != "None" and stat_z != "Match Rating":
                scatter_df[f"{stat_z} per 90"] = scatter_df[stat_z] / scatter_df["90s Played"].replace(0, 1)
                z_val = f"{stat_z} per 90"
            elif stat_z != "None":
                z_val = stat_z
        else:
            if stat_z != "None":
                z_val = stat_z

        if multi_season:
            scatter_df["Label"] = scatter_df["Player Name"] + " (" + scatter_df["Season"] + ")"
        else:
            scatter_df["Label"] = scatter_df["Player Name"]
            
        hover_data = ["Player Name", "Season", "Position 1", "Age", "Minutes Played"]

        if stat_z == "None":
            # 2D Plot
            fig = px.scatter(
                scatter_df, 
                x=x_val, 
                y=y_val, 
                color="Position 1",
                hover_name="Label",
                hover_data=hover_data
            )
            # Increased marker size to 20
            fig.update_traces(marker=dict(size=20, opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
            
            if show_trend:
                # Calculate overall trendline (ignoring groups)
                fig_trend = px.scatter(scatter_df, x=x_val, y=y_val, trendline="ols")
                # The second trace is the trendline (first is points)
                if len(fig_trend.data) > 1:
                    trend_trace = fig_trend.data[1]
                    trend_trace.line.color = 'white' # Visible on dark/light
                    trend_trace.name = "Overall Trend"
                    trend_trace.showlegend = True
                    fig.add_trace(trend_trace)
            
            if show_median:
                fig.add_hline(y=scatter_df[y_val].median(), line_dash="dash", line_color="gray", annotation_text="Median Y")
                fig.add_vline(x=scatter_df[x_val].median(), line_dash="dash", line_color="gray", annotation_text="Median X")
                
            st.plotly_chart(fig, use_container_width=True)
            
            # Correlation
            corr, _ = stats.pearsonr(scatter_df[x_val], scatter_df[y_val])
            st.metric("Correlation (Pearson)", f"{corr:.3f}")
            
        else:
            # 3D Plot
            fig = px.scatter_3d(
                scatter_df,
                x=x_val,
                y=y_val,
                z=z_val,
                color="Position 1",
                hover_name="Label",
                hover_data=hover_data
            )
            st.plotly_chart(fig, use_container_width=True)

        # Table - Show only selected stats
        cols_to_show_scatter = ["Player Name", "Season", "Position 1", "Nationality", "Age", "Minutes Played", x_val, y_val]
        if z_val:
            cols_to_show_scatter.append(z_val)
            
        st.dataframe(scatter_df[cols_to_show_scatter].style.format({x_val: "{:.2f}", y_val: "{:.2f}", z_val if z_val else "": "{:.2f}"}))

# === TAB 2: PLAYER COMPARISON ===
with tab2:
    st.header("Player Comparison (Radar)")
    
    # Select Players (Aggregated All Time or Specific Season?)
    # Usually comparison is best within a season, or selecting specific (Player, Season) tuples.
    # Let's list all (Player, Season) options.
    
    # Use global aggregated data from entire DF to ensure calculation of percentiles/max is correct relative to something?
    # Or just raw values? The prompt asks for Normalization.
    
    # Re-aggregate everything by Player+Season first
    all_players_agg = aggregate_stats(merged_df, ["Player Name", "Season"])
    all_players_agg["Unique Name"] = all_players_agg["Player Name"] + " (" + all_players_agg["Season"] + ")"
    
    col1, col2 = st.columns(2)
    selected_players = col1.multiselect("Select players to compare (2-3 recommended)", all_players_agg["Unique Name"].tolist(), max_selections=5)
    
    preset_cat = col2.selectbox("Category Preset", list(CATEGORY_PRESETS.keys()))
    
    opt_col1, opt_col2, opt_col3 = st.columns(3)
    use_per_90 = opt_col1.checkbox("Per 90", value=True)
    normalize = opt_col2.checkbox("Normalize (0-1)", value=True)
    fill_area = opt_col3.checkbox("Fill Area", value=True)
    
    # Filter Card / Edit Attributes
    with st.expander("Customize Attributes"):
        default_attrs = CATEGORY_PRESETS[preset_cat]
        selected_attrs = st.multiselect("Attributes", numeric_cols, default=[c for c in default_attrs if c in numeric_cols])

    if selected_players and selected_attrs:
        comparison_data = all_players_agg[all_players_agg["Unique Name"].isin(selected_players)].copy()
        
        # Prepare plotting data
        # We need to normalize relative to the MAX in the dataset (or the selected players?)
        # Standard radar charts usually normalize vs the whole population (dataset) to show "Good/Bad".
        
        # Calculate max for normalization across entire dataset (filtered by position maybe? keeping simple for now)
        
        radar_data = []
        
        for idx, row in comparison_data.iterrows():
            r_vals = []
            theta_vals = []
            
            for attr in selected_attrs:
                val = row[attr]
                
                if use_per_90 and attr != "Match Rating":
                    val = val / (row["90s Played"] if row["90s Played"] > 0 else 1)
                
                # Normalization
                if normalize:
                    # Get max of this attribute in the whole dataset
                    all_vals = all_players_agg[attr]
                    if use_per_90 and attr != "Match Rating":
                        all_vals = all_vals / all_players_agg["90s Played"].replace(0, 1)
                    
                    max_val = all_vals.max()
                    min_val = all_vals.min()
                    
                    if max_val - min_val > 0:
                        val = (val - min_val) / (max_val - min_val)
                    else:
                        val = 0
                
                r_vals.append(val)
                theta_vals.append(attr)
            
            # Close the loop
            r_vals.append(r_vals[0])
            theta_vals.append(theta_vals[0])
            
            radar_data.append(go.Scatterpolar(
                r=r_vals,
                theta=theta_vals,
                fill='toself' if fill_area else 'none',
                name=row["Unique Name"]
            ))

        # Radar Chart
        fig = go.Figure(data=radar_data)
        fig.update_layout(
            template="plotly_dark",
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 1] if normalize else None),
                bgcolor="rgba(0,0,0,0)"
            ),
            showlegend=True,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=600 # Bigger Radar
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Breakdown Table
        st.subheader("Stat Breakdown")
        breakdown = comparison_data[["Unique Name"] + selected_attrs].set_index("Unique Name").transpose()
        
        def highlight_text_max_min(s):
            is_max = s == s.max()
            is_min = s == s.min()
            return ['color: lightgreen' if v else 'color: lightcoral' if m else '' for v, m in zip(is_max, is_min)]
            
        st.dataframe(breakdown.style.apply(highlight_text_max_min, axis=1))

# === TAB 3: SCOUT REPORT ===


# === TAB 3: SCOUT REPORT ===
with tab3:
    st.header("Player Scout Report (Pizza Chart)")
    
    # Filters
    scout_col1, scout_col2 = st.columns(2)
    scout_seasons = sorted(merged_df["Season"].unique())
    if scout_seasons:
        scout_season = scout_col1.selectbox("Season", scout_seasons, index=len(scout_seasons)-1, key="scout_season")
    else:
        st.info("No seasons available.")
        st.stop()
    
    # Filter players by season
    season_players_df = merged_df[merged_df["Season"] == scout_season]
    # Re-aggregate for this season
    season_agg = aggregate_stats(season_players_df, ["Player Name"])
    
    scout_player = scout_col2.selectbox("Select Player", season_agg["Player Name"].unique())
    
    # Comparison Pool
    st.subheader("Comparison Pool")
    # Filter out None and ensure string
    avail_positions = sorted([str(p) for p in season_agg["Position 1"].unique() if p is not None])
    comp_pos = st.multiselect("Compare against Positions", avail_positions, default=avail_positions[:1] if avail_positions else None)
    
    if scout_player and comp_pos:
        player_row = season_agg[season_agg["Player Name"] == scout_player].iloc[0]
        
        # Pool
        pool_df = season_agg[season_agg["Position 1"].isin(comp_pos)]
        
        # Attributes for Pizza
        st.write("Configure Stats Categories")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            cats_pass = st.multiselect("Passing", numeric_cols, default=["Passes Completed", "Key Passes", "Assists"])
        with c2:
            cats_att = st.multiselect("Attacking", numeric_cols, default=["Goals", "Shots on Target", "Dribbles Completed"])
        with c3:
            cats_def = st.multiselect("Defending", numeric_cols, default=["Tackles Completed", "Interceptions", "Posession Won"])
        with c4:
            color_mode = st.radio("Color By", ["Category", "Percentile"], index=0)
            
        selected_cats = {"Passing": cats_pass, "Attacking": cats_att, "Defending": cats_def}
        
        # Calculate Percentiles
        pizza_labels = []
        pizza_values = [] # Percentiles
        pizza_texts = [] # Raw values
        colors = []
        
        cat_colors = {"Passing": "skyblue", "Attacking": "salmon", "Defending": "lightgreen"}
        
        for cat_name, items in selected_cats.items():
            for stat in items:
                # Player val
                p_val = player_row[stat]
                p_90s = player_row["90s Played"] if player_row["90s Played"] > 0 else 1
                p_metric = p_val / p_90s if stat != "Match Rating" else p_val
                
                # Pool vals
                pool_vals = pool_df[stat]
                if stat != "Match Rating":
                    pool_vals = pool_vals / pool_df["90s Played"].replace(0, 1)
                
                # Percentile
                if len(pool_vals) > 0:
                    percentile = stats.percentileofscore(pool_vals, p_metric)
                else:
                    percentile = 0
                
                pizza_labels.append(stat)
                pizza_values.append(percentile)
                # Value AND Percentile
                pizza_texts.append(f"{p_metric:.1f}<br>({int(percentile)}%)")
                
                if color_mode == "Category":
                    colors.append(cat_colors[cat_name])
                else:
                    # Will use colorscale in marker
                    pass
                
        # Plot Pizza (Bar Polar)
        marker_dict = dict(line=dict(color='white', width=1))
        if color_mode == "Category":
            marker_dict["color"] = colors
        else:
            marker_dict["color"] = pizza_values
            marker_dict["colorscale"] = "RdYlGn"
            marker_dict["cmin"] = 0
            marker_dict["cmax"] = 100
            marker_dict["showscale"] = True

        fig_pizza = go.Figure()
        
        # BarPolar Layer
        fig_pizza.add_trace(go.Barpolar(
            r=pizza_values,
            theta=pizza_labels,
            # text=pizza_texts, # Not needed in Barpolar if using Scatter for text
            marker=marker_dict,
            hoverinfo="text+theta+r", 
            hovertemplate="%{theta}: %{r:.1f}th Percentile<extra></extra>",
            name="Percentile"
        ))
        
        # Overlay Scatterpolar for Text Labels
        fig_pizza.add_trace(go.Scatterpolar(
            r=[v if v > 15 else 15 for v in pizza_values], # Ensure text is visible even for low values
            theta=pizza_labels,
            text=pizza_texts,
            mode="text",
            textfont=dict(size=11, color="white"),
            hoverinfo="skip", # Static labels
            showlegend=False
        ))
        
        fig_pizza.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=700, # Bigger chart
            font=dict(size=14),
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], showticklabels=False), # Hide radial ticks to unclutter
                angularaxis=dict(direction="clockwise"),
                bgcolor="rgba(0,0,0,0)"
            ),
            title=f"Scout Report: {scout_player} (vs {', '.join(comp_pos)})"
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
        
        # Report Card
        st.subheader("Detailed Report")
        report_data = {
            "Stat": pizza_labels,
            "Value (Per 90)": [f"{(player_row[stat] / (player_row['90s Played'] if player_row['90s Played']>0 else 1) if stat != 'Match Rating' else player_row[stat]):.2f}" for stat in pizza_labels],
            "Percentile": pizza_values
        }
        report_df = pd.DataFrame(report_data)
        st.dataframe(
            report_df,
            column_config={
                "Percentile": st.column_config.ProgressColumn(
                    "Percentile",
                    help="Player percentile rank vs pool",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
            },
            width='stretch'
        )
        
        # Pass Distribution
        st.subheader("Pass Distribution")
        pass_types = ["Short Passes", "Medium Passes", "Long Passes"]
        pass_cols = [(f"{pt} Attempted", f"{pt} Completed") for pt in pass_types]
        
        # Ensure cols exist
        valid_pass_types = [pt for pt in pass_types if f"{pt} Attempted" in player_row and f"{pt} Completed" in player_row]
        
        pass_df = pd.DataFrame({
            "Type": valid_pass_types,
            "Attempted": [player_row[f"{pt} Attempted"] for pt in valid_pass_types],
            "Completed": [player_row[f"{pt} Completed"] for pt in valid_pass_types]
        })
        pass_df["Completion %"] = (pass_df["Completed"] / pass_df["Attempted"].replace(0, 1)) * 100
        
        col_p1, col_p2 = st.columns(2)
        
        fig_pass = px.bar(pass_df, x="Type", y=["Completed", "Attempted"], barmode="group", title="Pass Types Volume", template="plotly_dark")
        fig_pass.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        col_p1.plotly_chart(fig_pass, use_container_width=True)
        
        col_p2.dataframe(
            pass_df,
            column_config={
                "Completion %": st.column_config.ProgressColumn(
                    "Completion %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                )
            },
            width='stretch'
        )

# --- Debug Section ---
st.markdown("---")
with st.expander("Debug: Data Diagnostics"):
    st.write("### Merge Diagnostics")
    st.write("If Positions/Nationality are 'None' or 'Unknown', the Player Name or Season might not match exactly between Squad and Match Stats.")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.write("#### Match Stats Keys (Name + Season)")
        ms_keys = match_stats_df[["Player Name", "Season"]].drop_duplicates().astype(str).sort_values("Player Name")
        st.dataframe(ms_keys, width='stretch')
        
    with c2:
        st.write("#### Squad Keys (Name + Season)")
        sq_keys = squad_info[["Player Name", "Season"]].drop_duplicates().astype(str).sort_values("Player Name")
        st.dataframe(sq_keys, width='stretch')
        
    st.write("### Raw Combined Data")
    st.dataframe(merged_df.head(50), width='stretch')
