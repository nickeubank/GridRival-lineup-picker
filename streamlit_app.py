import io

import gr_analytics
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

_sortable_list = components.declare_component(
    "sortable_driver_list",
    path="components/sortable_list",
)

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


@st.cache_data
def get_driver_data():
    df = gr_analytics.driver_data()
    latest_round = df["round"].max()
    return df[df["round"] == latest_round].copy()


def load_default_drivers():
    df = get_driver_data()
    df = df[df["type"] == "driver"].sort_values("eight_race_average").reset_index(drop=True)
    return [
        {
            "Position": i + 1,
            "Driver": row["driver_name"],
            "Team": row["driver_team"],
            "Abbr": row["driver_abbr"],
        }
        for i, (_, row) in enumerate(df.iterrows())
    ]


st.set_page_config(page_title="F1 GridRival Optimizer", page_icon="🏎️", layout="wide")

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


# Build locked-in picker options from driver data
dd = get_driver_data()
driver_rows = dd[dd["type"] == "driver"].sort_values("eight_race_average").reset_index(drop=True)
team_rows = dd[dd["type"] == "team"].sort_values("driver_name").reset_index(drop=True)

driver_label_to_abbr = {
    f"{r['driver_name']} ({r['driver_team']})": r["driver_abbr"]
    for _, r in driver_rows.iterrows()
}
abbr_to_team = {r["driver_abbr"]: r["driver_team"] for _, r in driver_rows.iterrows()}
team_abbrs = team_rows["driver_name"].tolist()

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("# 🏎️ F1 GridRival Lineup Optimizer")
st.markdown("Set your predicted race order and locked-in picks, then find the optimal lineup.")
st.markdown("---")

# ── Two-column layout ─────────────────────────────────────────────────────────

col_rank, col_picks = st.columns([3, 2])

with col_rank:
    st.markdown("### Predicted Race Finishing Order")

    result = _sortable_list(
        drivers=st.session_state.drivers,
        teamColors=TEAM_COLORS,
        key="race_order",
        default=None,
    )
    if result is not None:
        result = [dict(d) for d in result]
        if [d["Driver"] for d in result] != [d["Driver"] for d in st.session_state.drivers]:
            st.session_state.drivers = result
            st.rerun()

    st.markdown("")
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

with col_picks:
    st.markdown("### Locked-In Picks")
    st.markdown("Drivers and constructor already on your team.")

    st.markdown("**Drivers** (up to 5)")
    locked_driver_labels = []
    for label, abbr in driver_label_to_abbr.items():
        color = TEAM_COLORS.get(abbr_to_team.get(abbr, ""), "#555")
        col_bar, col_check = st.columns([0.04, 0.96])
        with col_bar:
            st.markdown(
                f"<div style='background:{color};width:5px;height:26px;"
                f"border-radius:3px;margin-top:4px;'></div>",
                unsafe_allow_html=True,
            )
        with col_check:
            if st.checkbox(label, key=f"lock_{abbr}"):
                locked_driver_labels.append(label)

    if len(locked_driver_labels) > 5:
        st.warning("Maximum 5 drivers allowed.")
        locked_driver_labels = locked_driver_labels[:5]

    locked_constructor = st.selectbox("Constructor", options=["(none)"] + team_abbrs)

    st.markdown("---")
    st.markdown("### Optimizer Settings")

    budget = st.number_input("Budget (£M)", min_value=50.0, max_value=200.0, value=100.0, step=0.1)
    optimize_for = st.selectbox("Optimise for", ["points", "salary_change"])

    if st.button("⚡ Find Optimal Lineup"):
        # Build locked_in list
        locked_in = [driver_label_to_abbr[lbl] for lbl in locked_driver_labels]
        if locked_constructor != "(none)":
            locked_in.append(locked_constructor)

        drivers = st.session_state.drivers
        n = len(drivers)

        scenario = pd.DataFrame({
            "driver_abbr": [d["Abbr"] for d in drivers],
            "qualifying_position": range(1, n + 1),
            "race_position": range(1, n + 1),
        })

        try:
            scored = gr_analytics.score_event(scenario)
            lineup = gr_analytics.optimal_lineup(
                scored,
                locked_in=locked_in if locked_in else None,
                optimize_for=optimize_for,
                budget=budget,
            )

            lineup_drivers = lineup[lineup["type"] == "driver"].sort_values("points_earned", ascending=False)
            lineup_team = lineup[lineup["type"] == "team"]

            total_pts = lineup["points_earned"].sum()
            star_row = lineup[lineup["star"] == 1]
            if not star_row.empty:
                total_pts += star_row.iloc[0]["points_earned"]  # star doubles their points

            total_salary = lineup["starting_salary"].sum()

            st.markdown("#### Optimal Lineup")

            for _, row in lineup_drivers.iterrows():
                team = row["driver_team"]
                color = TEAM_COLORS.get(team, "#ffffff")
                is_locked = row["driver_abbr"] in [driver_label_to_abbr[l] for l in locked_driver_labels]
                star = " ⭐" if row["star"] == 1 else ""
                lock = " 🔒" if is_locked else ""
                pts_display = int(row["points_earned"] * 2) if row["star"] == 1 else int(row["points_earned"])
                st.markdown(
                    f"<div style='background:#1a1a1a;border-left:4px solid {color};border-radius:6px;"
                    f"padding:10px 14px;margin:4px 0;display:flex;justify-content:space-between;'>"
                    f"<span><b style='color:#f0f0f0;'>{row['driver_name']}</b>"
                    f"<span style='color:{color};font-size:0.85em;margin-left:8px;'>{team}</span>"
                    f"<span style='color:#f5c518;'>{star}</span>"
                    f"<span style='color:#aaa;'>{lock}</span></span>"
                    f"<span style='color:#aaa;font-size:0.9em;'>£{row['starting_salary']}M &nbsp;|&nbsp; "
                    f"<b style='color:#e10600;'>{pts_display} pts</b></span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            for _, row in lineup_team.iterrows():
                color = TEAM_COLORS.get(row["driver_name"], "#ffffff")
                is_locked = locked_constructor == row["driver_name"]
                lock = " 🔒" if is_locked else ""
                st.markdown(
                    f"<div style='background:#1a1a1a;border-left:4px solid {color};border-radius:6px;"
                    f"padding:10px 14px;margin:4px 0;display:flex;justify-content:space-between;'>"
                    f"<span><b style='color:#f0f0f0;'>{row['driver_name']}</b>"
                    f"<span style='color:#aaa;font-size:0.85em;margin-left:8px;'>Constructor</span>"
                    f"<span style='color:#aaa;'>{lock}</span></span>"
                    f"<span style='color:#aaa;font-size:0.9em;'>£{row['starting_salary']}M &nbsp;|&nbsp; "
                    f"<b style='color:#e10600;'>{int(row['points_earned'])} pts</b></span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"<div style='margin-top:12px;padding:10px 14px;background:#222;border-radius:6px;"
                f"display:flex;justify-content:space-between;'>"
                f"<span style='color:#aaa;'>Salary: <b style='color:#f0f0f0;'>£{total_salary:.1f}M</b> / £{budget:.1f}M</span>"
                f"<span style='color:#aaa;'>Total pts: <b style='color:#e10600;font-size:1.1em;'>{int(total_pts)}</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        except Exception as e:
            st.error(f"Error: {e}")
