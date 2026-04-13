"""
Pitch visualisation helpers using mplsoccer.
Returns matplotlib Figure objects for embedding in Streamlit.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from mplsoccer import Pitch, VerticalPitch
from matplotlib.colors import LinearSegmentedColormap


# Arsenal colour palette
ARSENAL_RED    = "#EF0107"
ARSENAL_WHITE  = "#FFFFFF"
ARSENAL_GOLD   = "#9C824A"
BG_DARK        = "#0d1117"

ARSENAL_CMAP = LinearSegmentedColormap.from_list(
    "arsenal", ["#0d1117", ARSENAL_RED], N=256
)


def _base_pitch(vertical: bool = False, **kwargs) -> tuple:
    """Return a configured Pitch and (fig, ax)."""
    pitch_cls = VerticalPitch if vertical else Pitch
    pitch = pitch_cls(
        pitch_type="statsbomb",
        pitch_color=BG_DARK,
        line_color="#3d4450",
        linewidth=1.2,
        **kwargs,
    )
    fig, ax = pitch.draw(figsize=(10, 7) if not vertical else (7, 10))
    fig.patch.set_facecolor(BG_DARK)
    return pitch, fig, ax


def plot_press_heatmap(press_map: pd.DataFrame, team: str, match_label: str = "") -> plt.Figure:
    """Gaussian KDE heatmap of pressing locations."""
    pitch, fig, ax = _base_pitch()

    if press_map.empty:
        ax.text(60, 40, "No press data", color="white", ha="center", va="center", fontsize=14)
        return fig

    pitch.kdeplot(
        press_map["x"], press_map["y"],
        ax=ax,
        cmap=ARSENAL_CMAP,
        fill=True,
        alpha=0.75,
        levels=50,
        thresh=0.02,
    )

    title = f"{team} — Pressing Heatmap"
    if match_label:
        title += f"\n{match_label}"
    ax.set_title(title, color=ARSENAL_WHITE, fontsize=14, fontweight="bold", pad=12)

    # total press count annotation
    ax.text(
        119, 1, f"n={len(press_map)} pressures",
        color=ARSENAL_GOLD, fontsize=9, ha="right", va="bottom",
    )
    return fig


def plot_press_scatter(press_map: pd.DataFrame, team: str, match_label: str = "") -> plt.Figure:
    """Scatter of individual pressing events on pitch."""
    pitch, fig, ax = _base_pitch()

    if not press_map.empty:
        pitch.scatter(
            press_map["x"], press_map["y"],
            ax=ax,
            s=25,
            color=ARSENAL_RED,
            alpha=0.5,
            edgecolors="white",
            linewidths=0.3,
            zorder=3,
        )

    title = f"{team} — Individual Pressing Events"
    if match_label:
        title += f"\n{match_label}"
    ax.set_title(title, color=ARSENAL_WHITE, fontsize=13, fontweight="bold", pad=12)
    return fig


def plot_turnover_to_shot_map(sequences: pd.DataFrame, team: str) -> plt.Figure:
    """
    Arrow map: turnover location → shot location.
    Arrows coloured by xG of resulting shot.
    """
    pitch, fig, ax = _base_pitch()

    if sequences.empty:
        ax.text(60, 40, "No turnover→shot sequences found", color="white",
                ha="center", va="center", fontsize=12)
        ax.set_title(f"{team} — Turnover → Shot Sequences", color=ARSENAL_WHITE,
                     fontsize=13, fontweight="bold")
        return fig

    for _, row in sequences.iterrows():
        xg = row.get("shot_xg", 0.1) or 0.1
        color = plt.cm.RdYlGn(min(xg * 4, 1.0))  # green = high xG
        ax.annotate(
            "",
            xy=(row.get("shot_x", 100), row.get("shot_y", 40)),
            xytext=(row["turnover_x"], row["turnover_y"]),
            arrowprops=dict(
                arrowstyle="->",
                color=color,
                lw=1.5,
                connectionstyle="arc3,rad=0.15",
            ),
        )

    # plot turnover dots
    pitch.scatter(
        sequences["turnover_x"], sequences["turnover_y"],
        ax=ax, s=40, color=ARSENAL_RED, alpha=0.8,
        edgecolors="white", linewidths=0.4, zorder=4,
        label="Turnover location",
    )

    ax.set_title(
        f"{team} — Turnover → Shot ({len(sequences)} sequences)\n"
        "Arrow colour: green = higher xG",
        color=ARSENAL_WHITE, fontsize=12, fontweight="bold", pad=12,
    )
    return fig


def plot_press_by_minute(intensity_df: pd.DataFrame, team: str) -> plt.Figure:
    """Bar chart: pressing intensity by 5-minute bucket."""
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(BG_DARK)

    if intensity_df.empty:
        return fig

    ax.bar(
        intensity_df["minute_bucket"],
        intensity_df["presses"],
        width=4,
        color=ARSENAL_RED,
        alpha=0.85,
        edgecolor="#3d4450",
        linewidth=0.5,
    )

    ax.set_xlabel("Minute", color=ARSENAL_WHITE, fontsize=11)
    ax.set_ylabel("Pressures", color=ARSENAL_WHITE, fontsize=11)
    ax.set_title(f"{team} — Press Intensity by Game Minute", color=ARSENAL_WHITE,
                 fontsize=13, fontweight="bold")
    ax.tick_params(colors=ARSENAL_WHITE)
    for spine in ax.spines.values():
        spine.set_edgecolor("#3d4450")

    # mark halftime
    ax.axvline(45, color=ARSENAL_GOLD, linestyle="--", alpha=0.6, linewidth=1)
    ax.text(45.5, ax.get_ylim()[1] * 0.95, "HT", color=ARSENAL_GOLD, fontsize=8)

    fig.tight_layout()
    return fig
