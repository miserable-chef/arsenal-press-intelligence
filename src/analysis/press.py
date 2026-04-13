"""
High press analysis engine.

Measures:
  - Press intensity (pressures per possession sequence)
  - Win-ball zones (where on the pitch the team wins possession after pressing)
  - Press triggers (what events precede a successful press)
  - Turnover-to-shot sequences (how quickly a team shoots after winning possession)
  - PPDA (Passes Allowed Per Defensive Action) — standard press metric
"""

import numpy as np
import pandas as pd


# Pitch dimensions (StatsBomb standard)
PITCH_LENGTH = 120.0
PITCH_WIDTH  = 80.0

# Defensive thirds
DEFENSIVE_THIRD_X  = 40.0
MIDDLE_THIRD_X     = 80.0
ATTACKING_THIRD_X  = 120.0


def classify_pitch_zone(x: float, y: float) -> str:
    """Map (x, y) to a named pitch zone."""
    if x < DEFENSIVE_THIRD_X:
        zone = "Defensive Third"
    elif x < MIDDLE_THIRD_X:
        zone = "Middle Third"
    else:
        zone = "Attacking Third"

    if y < PITCH_WIDTH / 3:
        side = "Left"
    elif y < 2 * PITCH_WIDTH / 3:
        side = "Centre"
    else:
        side = "Right"

    return f"{zone} ({side})"


def compute_press_map(press_df: pd.DataFrame, team: str) -> pd.DataFrame:
    """
    Compute pressing location density for a team.
    Returns a dataframe with x, y, zone, count for heatmap rendering.
    """
    if press_df.empty:
        return pd.DataFrame()

    team_press = press_df[press_df["team"] == team].copy()
    if team_press.empty:
        return pd.DataFrame()

    def _get_zone(row):
        loc = row.get("location")
        try:
            if loc is not None and hasattr(loc, '__len__') and len(loc) >= 2:
                return classify_pitch_zone(float(loc[0]), float(loc[1]))
        except Exception:
            pass
        return classify_pitch_zone(
            float(row.get("location_x", 60)),
            float(row.get("location_y", 40)),
        )

    team_press["zone"] = team_press.apply(_get_zone, axis=1)

    # extract x, y safely — location may be a list, numpy array, or separate columns
    def safe_x(row):
        loc = row.get("location")
        try:
            if loc is not None and hasattr(loc, '__len__') and len(loc) >= 1:
                return float(loc[0])
        except Exception:
            pass
        return float(row.get("location_x", 60))

    def safe_y(row):
        loc = row.get("location")
        try:
            if loc is not None and hasattr(loc, '__len__') and len(loc) >= 2:
                return float(loc[1])
        except Exception:
            pass
        return float(row.get("location_y", 40))

    team_press["x"] = team_press.apply(safe_x, axis=1)
    team_press["y"] = team_press.apply(safe_y, axis=1)

    return team_press[["x", "y", "zone", "minute", "second", "player"]].reset_index(drop=True)


def compute_ppda(events_df: pd.DataFrame, team: str) -> float:
    """
    PPDA = Passes Allowed Per Defensive Action.
    Lower PPDA = more intense press.
    Measured in the opposition's defensive 60% of the pitch.
    """
    if events_df.empty:
        return np.nan

    def get_x(row):
        loc = row.get("location")
        try:
            if loc is not None and hasattr(loc, '__len__') and len(loc) >= 1:
                return float(loc[0])
        except Exception:
            pass
        return float(row.get("location_x", 60))

    events_df = events_df.copy()
    events_df["x"] = events_df.apply(get_x, axis=1)

    # opponent passes in their own 60%
    opp_team = [t for t in events_df["team"].unique() if t != team]
    if not opp_team:
        return np.nan
    opp = opp_team[0]

    opp_passes = events_df[
        (events_df["team"] == opp) &
        (events_df["type"] == "Pass") &
        (events_df["x"] < 72)  # their defensive 60%
    ]

    # team defensive actions (pressures, tackles, interceptions) in same zone
    defensive_actions = events_df[
        (events_df["team"] == team) &
        (events_df["type"].isin(["Pressure", "Tackle", "Interception", "Block"])) &
        (events_df["x"] > 48)  # high press zone
    ]

    if len(defensive_actions) == 0:
        return np.nan

    return round(len(opp_passes) / len(defensive_actions), 2)


def compute_turnover_to_shot(events_df: pd.DataFrame, team: str, max_seconds: int = 10) -> pd.DataFrame:
    """
    Find sequences where team wins possession via pressure/interception
    and results in a shot within max_seconds.
    Returns each such sequence with timing info.
    """
    if events_df.empty:
        return pd.DataFrame()

    events_sorted = events_df.sort_values(["minute", "second"]).reset_index(drop=True)
    events_sorted["time_seconds"] = events_sorted["minute"] * 60 + events_sorted["second"]

    win_possession_types = {"Pressure", "Interception", "Tackle", "Ball Recovery"}
    sequences = []

    for i, row in events_sorted.iterrows():
        if row.get("team") == team and row.get("type") in win_possession_types:
            t0 = row["time_seconds"]
            loc = row.get("location")
            try:
                if loc is not None and hasattr(loc, '__len__') and len(loc) >= 2:
                    win_x, win_y = float(loc[0]), float(loc[1])
                else:
                    win_x, win_y = 60.0, 40.0
            except Exception:
                win_x, win_y = 60.0, 40.0

            # look ahead for a shot by same team within max_seconds
            window = events_sorted[
                (events_sorted["team"] == team) &
                (events_sorted["type"] == "Shot") &
                (events_sorted["time_seconds"] > t0) &
                (events_sorted["time_seconds"] <= t0 + max_seconds)
            ]

            if not window.empty:
                shot = window.iloc[0]
                sequences.append({
                    "turnover_type": row["type"],
                    "turnover_x": win_x,
                    "turnover_y": win_y,
                    "turnover_minute": row["minute"],
                    "shot_minute": shot["minute"],
                    "seconds_to_shot": shot["time_seconds"] - t0,
                    "shot_outcome": shot.get("shot_outcome", ""),
                    "shot_xg": shot.get("shot_statsbomb_xg", np.nan),
                    "player": row.get("player", ""),
                })

    return pd.DataFrame(sequences)


def press_zone_summary(press_map: pd.DataFrame) -> pd.DataFrame:
    """Aggregate press counts by pitch zone for bar chart."""
    if press_map.empty:
        return pd.DataFrame()
    return (
        press_map.groupby("zone")
        .size()
        .reset_index(name="press_count")
        .sort_values("press_count", ascending=False)
    )


def compute_press_intensity_by_minute(press_map: pd.DataFrame) -> pd.DataFrame:
    """Press count per 5-minute bucket — shows when team presses hardest."""
    if press_map.empty:
        return pd.DataFrame()
    df = press_map.copy()
    df["minute_bucket"] = (df["minute"] // 5) * 5
    return (
        df.groupby("minute_bucket")
        .size()
        .reset_index(name="presses")
    )
