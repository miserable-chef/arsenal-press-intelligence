"""
StatsBomb open data loader.
Fetches competitions, matches, events and 360 frames.
Caches locally to avoid repeated API calls.
"""

import json
import pandas as pd
from pathlib import Path
from statsbombpy import sb

CACHE_DIR = Path(__file__).parents[2] / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_available_competitions() -> pd.DataFrame:
    """Return all StatsBomb open data competitions."""
    return sb.competitions()


def get_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    return sb.matches(competition_id=competition_id, season_id=season_id)


def get_events(match_id: int, split: bool = False) -> pd.DataFrame | dict:
    cache = CACHE_DIR / f"events_{match_id}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    events = sb.events(match_id=match_id, split=split, flatten_attrs=True)
    if isinstance(events, pd.DataFrame):
        events.to_parquet(cache, index=False)
    return events


def get_frames(match_id: int) -> pd.DataFrame:
    """Load StatsBomb 360 freeze-frame data (all player positions per event)."""
    cache = CACHE_DIR / f"frames_{match_id}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    try:
        frames = sb.frames(match_id=match_id, fmt="dataframe")
        frames.to_parquet(cache, index=False)
        return frames
    except Exception:
        return pd.DataFrame()


def get_lineups(match_id: int) -> dict:
    return sb.lineups(match_id=match_id)


# ── convenience: get all matches for a team across open competitions ──────────

def find_team_matches(team_name: str) -> pd.DataFrame:
    """Find all StatsBomb open data matches involving a team."""
    comps = get_available_competitions()
    rows = []
    for _, comp in comps.iterrows():
        try:
            matches = get_matches(comp.competition_id, comp.season_id)
            team_matches = matches[
                (matches.home_team == team_name) | (matches.away_team == team_name)
            ]
            if not team_matches.empty:
                team_matches = team_matches.copy()
                team_matches["competition"] = comp.competition_name
                team_matches["season"] = comp.season_name
                rows.append(team_matches)
        except Exception:
            continue
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def get_press_events(match_id: int) -> pd.DataFrame:
    """Extract all pressing events from a match."""
    events = get_events(match_id)
    if events.empty:
        return pd.DataFrame()
    press = events[events["type"] == "Pressure"].copy()
    return press


def get_shot_events(match_id: int) -> pd.DataFrame:
    """Extract all shot events including xG."""
    events = get_events(match_id)
    if events.empty:
        return pd.DataFrame()
    shots = events[events["type"] == "Shot"].copy()
    return shots


if __name__ == "__main__":
    comps = get_available_competitions()
    print(f"Available competitions: {len(comps)}")
    print(comps[["competition_id", "season_id", "competition_name", "season_name"]].to_string())
