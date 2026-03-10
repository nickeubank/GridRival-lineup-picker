import io

import pandas as pd
import streamlit as st

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
.driver-card {
    background: #1a1a1a;
    border-radius: 8px;
    padding: 10px 16px;
    margin: 4px 0;
    display: flex;
    align-items: center;
    border-left: 4px solid #e10600;
}
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
if "selected" not in st.session_state:
    st.session_state.selected = None


def move_driver(index, direction):
    drivers = st.session_state.drivers
    swap_index = index + direction
    if 0 <= swap_index < len(drivers):
        drivers[index], drivers[swap_index] = drivers[swap_index], drivers[index]
        for i, d in enumerate(drivers):
            d["Position"] = i + 1
        st.session_state.selected = swap_index


def reset_order():
    st.session_state.drivers = DEFAULT_DRIVERS.copy()
    st.session_state.selected = None


# Header
st.markdown("# 🏎️ F1 Driver Ranker")
st.markdown("Reorder the drivers using the arrows, then download your ranking as a CSV.")
st.markdown("---")

# Driver list
drivers = st.session_state.drivers

for i, driver in enumerate(drivers):
    team = driver["Team"]
    color = TEAM_COLORS.get(team, "#ffffff")
    is_selected = st.session_state.selected == i

    bg = "#2a2a2a" if is_selected else "#1a1a1a"
    border = color

    col_pos, col_info, col_up, col_down = st.columns([0.8, 5, 0.7, 0.7])

    with col_pos:
        st.markdown(
            f"<div style='background:{bg};border-left:4px solid {border};border-radius:6px;"
            f"padding:10px 8px;text-align:center;font-size:1.2em;font-weight:bold;color:#e10600;'>"
            f"P{driver['Position']}</div>",
            unsafe_allow_html=True,
        )

    with col_info:
        st.markdown(
            f"<div style='background:{bg};border-left:4px solid {border};border-radius:6px;"
            f"padding:10px 14px;'>"
            f"<span style='font-weight:bold;font-size:1em;color:#f0f0f0;'>{driver['Driver']}</span>"
            f"<span style='color:{color};font-size:0.85em;margin-left:10px;'>{team}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_up:
        if i > 0:
            if st.button("▲", key=f"up_{i}"):
                move_driver(i, -1)
                st.rerun()
        else:
            st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)

    with col_down:
        if i < len(drivers) - 1:
            if st.button("▼", key=f"down_{i}"):
                move_driver(i, 1)
                st.rerun()
        else:
            st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)

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
    csv_data = csv_buffer.getvalue()

    st.download_button(
        label="⬇️ Download Ranking as CSV",
        data=csv_data,
        file_name="f1_driver_ranking.csv",
        mime="text/csv",
    )
