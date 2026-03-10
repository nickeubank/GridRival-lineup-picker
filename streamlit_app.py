import io

import gr_analytics
import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items

TEAM_COLORS = {
    "RBR": "#3671C6",
    "MCL": "#FF8000",
    "FER": "#E8002D",
    "MER": "#27F4D2",
    "AMR": "#229971",
    "ALP": "#FF87BC",
    "HAS": "#B6BABD",
    "AUD": "#52E252",
    "WIL": "#64C4FF",
    "RBS": "#6692FF",
    "CAD": "#CC0000",
}


def load_default_drivers():
    df = gr_analytics.driver_data()
    latest_round = df["round"].max()
    df = df[(df["round"] == latest_round) & (df["type"] == "driver")]
    df = df.sort_values("eight_race_average").reset_index(drop=True)
    return [
        {
            "Position": i + 1,
            "Driver": row["driver_name"],
            "Team": row["driver_team"],
            "Abbr": row["driver_abbr"],
        }
        for i, (_, row) in enumerate(df.iterrows())
    ]


st.set_page_config(page_title="F1 Driver Ranker", page_icon="🏎️", layout="centered")

st.markdown(
    """
<style>
.main { background-color: #0f0f0f; }
.stApp { background-color: #0f0f0f; color: #f0f0f0; }
h1, h2, h3 { color: #e10600; font-family: 'Formula1', sans-serif; }
.stButton > button {
    background-color: #e10600;
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #b30500;
    color: white;
}
.stDownloadButton > button {
    background-color: #e10600 !important;
    color: white !important;
    font-weight: bold;
}
</style>
""",
    unsafe_allow_html=True,
)

# Init state
if "drivers" not in st.session_state:
    st.session_state.drivers = load_default_drivers()


def reset_order():
    st.session_state.drivers = load_default_drivers()


# Header
st.markdown("# 🏎️ F1 GridRival Lineup Optimizer")
st.markdown("Drag drivers into your predicted race finishing order, then find the optimal lineup.")
st.markdown("---")

# ── Drag-and-drop ranking ─────────────────────────────────────────────────────

items = [f"P{d['Position']}  {d['Driver']}  —  {d['Team']}" for d in st.session_state.drivers]
name_to_driver = {d["Driver"]: d for d in st.session_state.drivers}

sorted_items = sort_items(items, direction="vertical")


def parse_name(item_str):
    return item_str.split("  —  ")[0].split("  ", 1)[1]


sorted_names = [parse_name(s) for s in sorted_items]
current_names = [d["Driver"] for d in st.session_state.drivers]

if sorted_names != current_names:
    st.session_state.drivers = [
        {**name_to_driver[name], "Position": i + 1}
        for i, name in enumerate(sorted_names)
    ]
    st.rerun()

st.markdown("---")

# ── Actions row ───────────────────────────────────────────────────────────────

col_reset, col_dl = st.columns([1, 2])

with col_reset:
    if st.button("🔄 Reset to Default"):
        reset_order()
        st.rerun()

with col_dl:
    df_dl = pd.DataFrame(st.session_state.drivers)
    csv_buffer = io.StringIO()
    df_dl.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download Ranking as CSV",
        data=csv_buffer.getvalue(),
        file_name="f1_driver_ranking.csv",
        mime="text/csv",
    )

# ── Optimal lineup ────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Find Optimal Lineup")

col_budget, col_opt = st.columns([1, 1])
with col_budget:
    budget = st.number_input("Budget (£M)", min_value=50.0, max_value=200.0, value=100.0, step=0.1)
with col_opt:
    optimize_for = st.selectbox("Optimise for", ["points", "salary_change"])

if st.button("⚡ Find Optimal Lineup"):
    drivers = st.session_state.drivers
    n = len(drivers)

    scenario = pd.DataFrame({
        "driver_abbr": [d["Abbr"] for d in drivers],
        "qualifying_position": range(1, n + 1),
        "race_position": range(1, n + 1),
    })

    try:
        scored = gr_analytics.score_event(scenario)
        lineup = gr_analytics.optimal_lineup(scored, optimize_for=optimize_for, budget=budget)

        lineup_drivers = lineup[lineup["type"] == "driver"].sort_values("points_earned", ascending=False)
        lineup_team = lineup[lineup["type"] == "team"]

        st.markdown("#### Optimal Lineup")

        total_pts = lineup["points_earned"].sum()
        star_row = lineup[lineup["star"] == 1]
        if not star_row.empty:
            star_abbr = star_row.iloc[0]["driver_abbr"]
            star_pts = star_row.iloc[0]["points_earned"]
            total_pts += star_pts  # star doubles their points

        total_salary = lineup["starting_salary"].sum()

        for _, row in lineup_drivers.iterrows():
            team = row["driver_team"]
            color = TEAM_COLORS.get(team, "#ffffff")
            star = " ⭐ STAR" if row["star"] == 1 else ""
            pts_display = int(row["points_earned"] * 2) if row["star"] == 1 else int(row["points_earned"])
            st.markdown(
                f"<div style='background:#1a1a1a;border-left:4px solid {color};border-radius:6px;"
                f"padding:10px 14px;margin:4px 0;display:flex;justify-content:space-between;'>"
                f"<span><b style='color:#f0f0f0;'>{row['driver_name']}</b>"
                f"<span style='color:{color};font-size:0.85em;margin-left:10px;'>{team}</span>"
                f"<span style='color:#f5c518;'>{star}</span></span>"
                f"<span style='color:#aaa;font-size:0.9em;'>£{row['starting_salary']}M &nbsp;|&nbsp; "
                f"<b style='color:#e10600;'>{pts_display} pts</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        for _, row in lineup_team.iterrows():
            color = TEAM_COLORS.get(row["driver_name"], "#ffffff")
            st.markdown(
                f"<div style='background:#1a1a1a;border-left:4px solid {color};border-radius:6px;"
                f"padding:10px 14px;margin:4px 0;display:flex;justify-content:space-between;'>"
                f"<span><b style='color:#f0f0f0;'>{row['driver_name']}</b>"
                f"<span style='color:#aaa;font-size:0.85em;margin-left:10px;'>Constructor</span></span>"
                f"<span style='color:#aaa;font-size:0.9em;'>£{row['starting_salary']}M &nbsp;|&nbsp; "
                f"<b style='color:#e10600;'>{int(row['points_earned'])} pts</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div style='margin-top:12px;padding:10px 14px;background:#222;border-radius:6px;"
            f"display:flex;justify-content:space-between;'>"
            f"<span style='color:#aaa;'>Total salary: <b style='color:#f0f0f0;'>£{total_salary:.1f}M</b> / £{budget}M</span>"
            f"<span style='color:#aaa;'>Total points: <b style='color:#e10600;font-size:1.1em;'>{int(total_pts)}</b></span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    except Exception as e:
        st.error(f"Scoring error: {e}")
