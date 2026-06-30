import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from auth import require_login
from ui_theme import apply_global_style, page_header, render_table


st.set_page_config(page_title="Sheffield Map Visualisation", page_icon=":world_map:", layout="wide")
apply_global_style()
require_login()

page_header(
    "MP",
    "Sheffield Disaster Map Visualisation",
)

results = st.session_state["simulation_results"]
allocation = results.get("allocation_result", {})
scenario = allocation.get("scenario", {})
solvers = allocation.get("solvers", {})
assignments = solvers.get("classical-optimal-flow", {}).get("assignments", [])


st.subheader("Sheffield city response map")

scenario = allocation.get("scenario", {})

base_location = scenario.get("location")
if not isinstance(base_location, list) or len(base_location) != 2:
    base_location = [53.3811, -1.4701]

m = folium.Map(
    location=base_location,
    zoom_start=12,
    tiles="OpenStreetMap",
)

for inc in scenario.get("incidents", []):
    if inc is None:
        continue

    folium.Marker(
        location=[inc.get("lat", 0), inc.get("lon", 0)],
        popup=f"Incident {inc.get('id', 'NA')} ({inc.get('severity_level', 'NA')})",
        icon=folium.Icon(color="red"),
    ).add_to(m)

for a in scenario.get("ambulances", []):
    if a is None:
        continue

    folium.Marker(
        location=[a.get("lat", 0), a.get("lon", 0)],
        popup=f"Ambulance {a.get('id', 'NA')}",
        icon=folium.Icon(color="blue"),
    ).add_to(m)

for assign in assignments:
    amb = next(
        (x for x in scenario.get("ambulances", []) if x["id"] == assign.get("ambulance_id")),
        None
    )
    inc = next(
        (x for x in scenario.get("incidents", []) if x["id"] == assign.get("incident_id")),
        None
    )

    if amb and inc:
        folium.PolyLine(
            locations=[
                [amb.get("lat", 0), amb.get("lon", 0)],
                [inc.get("lat", 0), inc.get("lon", 0)],
            ],
            color="green",
            weight=3,
        ).add_to(m)

# DISASTER INPUT LOCATION (from UI)
if isinstance(base_location, list) and len(base_location) == 2:
    folium.Circle(
        location=base_location,
        radius=1200,
        popup="Disaster Input Location",
        color="purple",
        fill=True,
        fill_opacity=0.18,
    ).add_to(m)

folium.Circle(
    location=[53.3811, -1.4701],
    radius=6500,
    popup="Sheffield city operating area",
    color="#1f8a70",
    fill=False,
    weight=3,
).add_to(m)

st_folium(m, width=1100, height=560)

st.subheader("Sheffield Location Risk Data")
incident_table = pd.DataFrame([
    {
        "ID": inc.get("id"),
        "Severity": inc.get("severity_level"),
        "Lat": inc.get("lat"),
        "Lon": inc.get("lon"),
        "Category": inc.get("category"),
    }
    for inc in scenario.get("incidents", [])
])

render_table(incident_table)

