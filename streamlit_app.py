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
        {"Position": i + 1, "Driver": row["driver_name"], "Team": row["driver_team"]}
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
st.markdown("# 🏎️ F1 Driver Ranker")
st.markdown("Drag and drop drivers to reorder, then download your ranking as a CSV.")
st.markdown("---")

# Build display strings — driver name is the unique key used to parse back
items = [f"P{d['Position']}  {d['Driver']}  —  {d['Team']}" for d in st.session_state.drivers]
name_to_driver = {d["Driver"]: d for d in st.session_state.drivers}

sorted_items = sort_items(items, direction="vertical")


def parse_name(item_str):
    # format: "P1  M. Verstappen  —  RBR"
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

# Actions row
col_reset, col_dl = st.columns([1, 2])

with col_reset:
    if st.button("🔄 Reset to Default"):
        reset_order()
        st.rerun()

with col_dl:
    df = pd.DataFrame(st.session_state.drivers)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="⬇️ Download Ranking as CSV",
        data=csv_buffer.getvalue(),
        file_name="f1_driver_ranking.csv",
        mime="text/csv",
    )
