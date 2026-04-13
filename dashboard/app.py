"""
Arsenal Press Intelligence Dashboard
Powered by StatsBomb open data + mplsoccer
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px

from src.data.loader import (
    get_available_competitions, get_matches, get_events,
    get_press_events, get_shot_events, find_team_matches,
)
from src.analysis.press import (
    compute_press_map, compute_ppda, compute_turnover_to_shot,
    press_zone_summary, compute_press_intensity_by_minute,
)
from src.viz.pitch_plots import (
    plot_press_heatmap, plot_press_scatter,
    plot_turnover_to_shot_map, plot_press_by_minute,
)

st.set_page_config(
    page_title="Arsenal Press Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

ARSENAL_RED = "#EF0107"
BG = "#0d1117"

st.markdown(f"""
<style>
.stApp {{ background-color: {BG}; }}
h1, h2, h3 {{ color: white; }}
.metric-label {{ color: #9C824A !important; }}
</style>
""", unsafe_allow_html=True)


# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"<h2 style='color:{ARSENAL_RED}'>⚽ Arsenal Press Intelligence</h2>", unsafe_allow_html=True)
    st.caption("StatsBomb 360 open data · mplsoccer")
    st.divider()

    @st.cache_data(show_spinner=False)
    def load_competitions():
        return get_available_competitions()

    comps = load_competitions()

    comp_options = comps[["competition_id", "season_id", "competition_name", "season_name"]].copy()
    comp_options["label"] = comp_options["competition_name"] + " — " + comp_options["season_name"]
    comp_label = st.selectbox("Competition", comp_options["label"].tolist())

    selected = comp_options[comp_options["label"] == comp_label].iloc[0]
    comp_id = int(selected["competition_id"])
    season_id = int(selected["season_id"])

    @st.cache_data(show_spinner=False)
    def load_matches(cid, sid):
        return get_matches(cid, sid)

    matches_df = load_matches(comp_id, season_id)

    all_teams = sorted(set(matches_df["home_team"].tolist() + matches_df["away_team"].tolist()))
    team = st.selectbox("Team", all_teams,
                        index=all_teams.index("Arsenal") if "Arsenal" in all_teams else 0)

    team_matches = matches_df[
        (matches_df["home_team"] == team) | (matches_df["away_team"] == team)
    ].copy()
    team_matches["label"] = team_matches.apply(
        lambda r: f"{r['home_team']} {r['home_score']}–{r['away_score']} {r['away_team']} (MD{r['match_week']})",
        axis=1,
    )

    match_label = st.selectbox("Match", team_matches["label"].tolist())
    match_row = team_matches[team_matches["label"] == match_label].iloc[0]
    match_id = int(match_row["match_id"])

    max_seconds = st.slider("Turnover→Shot window (secs)", 5, 20, 10)
    st.divider()
    st.markdown("**Data:** StatsBomb open data\n\n**Stack:** statsbombpy · mplsoccer · Streamlit")


# ── load match data ───────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Loading match events…")
def load_match_data(mid):
    events  = get_events(mid)
    presses = get_press_events(mid)
    shots   = get_shot_events(mid)
    return events, presses, shots

with st.spinner("Loading match data…"):
    events, presses, shots = load_match_data(match_id)

press_map   = compute_press_map(presses, team)
ppda        = compute_ppda(events, team)
sequences   = compute_turnover_to_shot(events, team, max_seconds)
zone_counts = press_zone_summary(press_map)
intensity   = compute_press_intensity_by_minute(press_map)


# ── header ────────────────────────────────────────────────────────────────────
st.markdown(f"<h1 style='color:{ARSENAL_RED}'>Arsenal Press Intelligence</h1>", unsafe_allow_html=True)
st.caption(f"{match_label} · StatsBomb open data")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pressures", len(press_map) if not press_map.empty else 0)
c2.metric("PPDA", f"{ppda:.2f}" if ppda == ppda else "N/A",
          help="Passes Allowed Per Defensive Action — lower = more intense press")
c3.metric("Turnover→Shot Sequences", len(sequences))
c4.metric("Avg xG from Turnovers",
          f"{sequences['shot_xg'].mean():.3f}" if not sequences.empty and sequences['shot_xg'].notna().any() else "N/A")
st.divider()


# ── tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["Press Heatmap", "Press Scatter", "Turnover→Shot", "Intensity"])

with tab1:
    st.subheader("Pressing Heatmap")
    st.caption("Gaussian KDE of all pressing events — darker red = higher press density")
    fig = plot_press_heatmap(press_map, team, match_label)
    st.pyplot(fig, use_container_width=True)

    if not zone_counts.empty:
        st.subheader("Press Count by Zone")
        fig2 = px.bar(
            zone_counts, x="zone", y="press_count",
            color="press_count",
            color_continuous_scale=[[0, "#1a1a2e"], [1, ARSENAL_RED]],
            labels={"press_count": "Pressures", "zone": "Zone"},
        )
        fig2.update_layout(
            paper_bgcolor=BG, plot_bgcolor=BG,
            font_color="white", showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Individual Pressing Events")
    st.caption("Each dot = one pressure event")
    fig = plot_press_scatter(press_map, team, match_label)
    st.pyplot(fig, use_container_width=True)

with tab3:
    st.subheader(f"Turnover → Shot within {max_seconds}s")
    st.caption("Arrows show sequences: win possession → shot. Green arrow = higher xG.")
    fig = plot_turnover_to_shot_map(sequences, team)
    st.pyplot(fig, use_container_width=True)

    if not sequences.empty:
        st.dataframe(
            sequences[["turnover_type", "turnover_minute", "seconds_to_shot",
                        "shot_xg", "shot_outcome", "player"]].round(3),
            use_container_width=True, hide_index=True,
            column_config={
                "shot_xg": st.column_config.ProgressColumn("xG", min_value=0, max_value=1, format="%.3f"),
                "seconds_to_shot": st.column_config.NumberColumn("Secs to Shot", format="%.1f"),
            }
        )

with tab4:
    st.subheader("Press Intensity by Game Minute")
    st.caption("Pressures per 5-minute bucket — shows when the team presses hardest")
    fig = plot_press_by_minute(intensity, team)
    st.pyplot(fig, use_container_width=True)

    if not intensity.empty:
        first_half  = intensity[intensity["minute_bucket"] < 45]["presses"].sum()
        second_half = intensity[intensity["minute_bucket"] >= 45]["presses"].sum()
        h1, h2 = st.columns(2)
        h1.metric("First Half Pressures",  int(first_half))
        h2.metric("Second Half Pressures", int(second_half))
