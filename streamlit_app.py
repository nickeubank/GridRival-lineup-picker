import io

import pandas as pd
import streamlit as st
from streamlit_sortables import sort_items

# 2024 F1 Driver Lineup
DEFAULT_DRIVERS = [
    {"Position": 1, "Driver": "Max Verstappen", "Team": "Red Bull Racing"},
    {"Position": 2, "Driver": "Lando Norris", "Team": "McLaren"},
    {"Position": 3, "Driver": "Charles Leclerc", "Team": "Ferrari"},
    {"Position": 4, "Driver": "Oscar Piastri", "Team": "McLaren"},
    {"Position": 5, "Driver": "Carlos Sainz", "Team": "Ferrari"},
    {"Position": 6, "Driver": "George Russell", "Team": "Mercedes"},
    {"Position": 7, "Driver": "Lewis Hamilton", "Team": "Mercedes"},
    {"Position": 8, "Driver": "Sergio Perez", "Team": "Red Bull Racing"},
    {"Position": 9, "Driver": "Fernando Alonso", "Team": "Aston Martin"},
    {"Position": 10, "Driver": "Lance Stroll", "Team": "Aston Martin"},
    {"Position": 11, "Driver": "Esteban Ocon", "Team": "Alpine"},
    {"Position": 12, "Driver": "Pierre Gasly", "Team": "Alpine"},
    {"Position": 13, "Driver": "Nico Hulkenberg", "Team": "Haas"},
    {"Position": 14, "Driver": "Kevin Magnussen", "Team": "Haas"},
    {"Position": 15, "Driver": "Valtteri Bottas", "Team": "Sauber"},
    {"Position": 16, "Driver": "Guanyu Zhou", "Team": "Sauber"},
    {"Position": 17, "Driver": "Alexander Albon", "Team": "Williams"},
    {"Position": 18, "Driver": "Franco Colapinto", "Team": "Williams"},
    {"Position": 19, "Driver": "Yuki Tsunoda", "Team": "RB"},
    {"Position": 20, "Driver": "Liam Lawson", "Team": "RB"},
]

TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "McLaren": "#FF8000",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Haas": "#B6BABD",
    "Sauber": "#52E252",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
}

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
    st.session_state.drivers = DEFAULT_DRIVERS.copy()


def reset_order():
    st.session_state.drivers = DEFAULT_DRIVERS.copy()


# Header
st.markdown("# 🏎️ F1 Driver Ranker")
st.markdown("Drag and drop drivers to reorder, then download your ranking as a CSV.")
st.markdown("---")

# Build display strings — driver name is the unique key used to parse back
items = [f"P{d['Position']}  {d['Driver']}  —  {d['Team']}" for d in st.session_state.drivers]
name_to_driver = {d["Driver"]: d for d in DEFAULT_DRIVERS}

sorted_items = sort_items(items, direction="vertical")

# Parse driver name back out and update session state if order changed
def parse_name(item_str):
    # format: "P1  Max Verstappen  —  Red Bull Racing"
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
