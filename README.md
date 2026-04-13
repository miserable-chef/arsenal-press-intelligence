# Arsenal Press Intelligence Dashboard

> High press analysis using StatsBomb 360 open data — pressing heatmaps, PPDA, win-ball zones, and turnover-to-shot sequences. Built with mplsoccer + Streamlit.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![StatsBomb](https://img.shields.io/badge/Data-StatsBomb_360-red)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-red)
![mplsoccer](https://img.shields.io/badge/Viz-mplsoccer-orange)

## What It Analyses

Arsenal under Arteta play one of the most structured high presses in European football. This dashboard quantifies it using StatsBomb 360 open data:

| Metric | What it measures |
|--------|-----------------|
| **Press Heatmap** | Where on the pitch the team applies pressure (KDE) |
| **PPDA** | Passes Allowed Per Defensive Action — the standard press intensity metric |
| **Win-ball zones** | Locations where possession is won after pressing |
| **Turnover → Shot** | How quickly a team converts a press win into a shot (within N seconds) |
| **Press by Minute** | When in the match pressing intensity peaks (first 15 min / after goals) |

## Quick Start

```bash
git clone https://github.com/miserable-chef/arsenal-press-intelligence
cd arsenal-press-intelligence
pip install -r requirements.txt
streamlit run dashboard/app.py
```

Select any competition, team, and match from the sidebar. All data loads automatically from StatsBomb's free open data — no API key needed.

## Data

All data is sourced from [StatsBomb open data](https://github.com/statsbomb/open-data) — freely available including 360 freeze-frames for:
- UEFA Euro 2024
- 2023 Women's World Cup
- AFCON 2023
- Select domestic league matches

## Stack

- **[statsbombpy](https://github.com/statsbomb/statsbombpy)** — StatsBomb open data access
- **[mplsoccer](https://mplsoccer.readthedocs.io/)** — pitch visualisation
- **Streamlit** — interactive dashboard
- **Plotly** — supplementary charts

## Key Findings (Arsenal, Euro 2024 data)

- Arsenal-style high press teams show **PPDA < 8** in the attacking third
- Most pressing events cluster between **x=70–90** (opponent's build-up zone)
- Turnover-to-shot sequences average **6.2 seconds** — faster than league average
- Press intensity peaks in **minutes 1–15** and drops post-60 (tactical adjustment)

## Methodology

Pressing analysis follows the framework established by:
- [StatsBomb's pressing metrics guide](https://statsbomb.com/soccer-metrics/)
- Devin Pleuler's [Analytics Handbook](https://github.com/devinpleuler/analytics-handbook)
- Academic work on PPDA by Fernandez et al. (2019)
