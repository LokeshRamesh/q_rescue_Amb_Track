import math
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from ambulance_data import available_ambulance_count, build_ambulance_routes
from auth import require_login
from ui_theme import apply_global_style, page_header, render_table


st.set_page_config(
    page_title="Hospital & Ambulance Tracker",
    page_icon=":ambulance:",
    layout="wide",
)
apply_global_style()
require_login()

page_header("A+", "Sheffield Hospital & Ambulance Tracker")

results = st.session_state.get("simulation_results", {})
allocation = results.get("allocation_result", {})
scenario = allocation.get("scenario", {})

incidents = scenario.get("incidents", [])
ambulances = scenario.get("ambulances", [])


control_col1, control_col2 = st.columns(2)
with control_col1:
    live_refresh = st.toggle("Live refresh", value=True)
with control_col2:
    refresh_seconds = st.selectbox("Refresh every", [5, 10, 15, 30], index=1)

def build_live_hospital_data(base_data, ambulance_data, tick):
    hospitals = base_data.copy()
    assigned_counts = ambulance_data.get("Assigned Hospital", pd.Series()).value_counts()

    spaces = []
    statuses = []

    for index, row in hospitals.iterrows():
        available_spaces = max(
            0,
            min(
                int(row["Total Spaces"]),
                int(row["Base Spaces"]) + ((tick + index * 4) % 17) - 8,
            ),
        )

        if available_spaces <= 4:
            status = "Critical"
        elif available_spaces <= 10:
            status = "Limited"
        else:
            status = "Open"

        spaces.append(available_spaces)
        statuses.append(status)

    hospitals["Available Spaces"] = spaces
    hospitals["Ambulances Available"] = (
        hospitals["Hospital"].map(assigned_counts).fillna(0).astype(int)
    )
    hospitals["Status"] = statuses

    return hospitals.drop(columns=["Base Spaces", "Base Ambulances"])

@st.cache_data
def cached_hospital_sim(base_data, ambulance_data, tick):
    return build_live_hospital_data(base_data, ambulance_data, tick)

def build_live_ambulance_data(base_data, tick, updated_time):
    ambulances = base_data.copy()

    speeds = []
    statuses = []
    latitudes = []
    longitudes = []

    for index, row in ambulances.iterrows():
        phase = tick + index * 3
        status_cycle = phase % 6

        if status_cycle in (0, 1, 2):
            status = "On Route"
            speed = 24 + ((phase * 7) % 28)
        elif status_cycle in (3, 4):
            status = "Available"
            speed = 0
        else:
            status = "Busy"
            speed = 12 + ((phase * 5) % 18)

        latitudes.append(row["lat"] if "lat" in row else row["Latitude"] + math.sin(phase * 0.55) * 0.006)
        longitudes.append(row["lon"] if "lon" in row else row["Longitude"] + math.cos(phase * 0.55) * 0.008)
        speeds.append(speed)
        statuses.append(status)

    ambulances["Latitude"] = latitudes
    ambulances["Longitude"] = longitudes
    ambulances["Speed mph"] = speeds
    ambulances["Availability"] = statuses
    ambulances["Updated"] = updated_time

    return ambulances


@st.cache_data
def cached_ambulance_sim(base_data, tick, updated_time):
    return build_live_ambulance_data(base_data, tick, updated_time)

@st.fragment(run_every=refresh_seconds if live_refresh else None)
def live_tracker():
    updated_at = datetime.now()
    tick = int(updated_at.timestamp() // refresh_seconds)
    updated_time = updated_at.strftime("%H:%M:%S")
    base_hospitals = pd.DataFrame([
        {
            "Hospital": "Northern General Hospital",
            "Latitude": 53.4109,
            "Longitude": -1.4587,
            "Total Spaces": 120,
            "Base Spaces": 34,
            "Base Ambulances": 8,
        },
        {
            "Hospital": "Royal Hallamshire Hospital",
            "Latitude": 53.3785,
            "Longitude": -1.4939,
            "Total Spaces": 95,
            "Base Spaces": 22,
            "Base Ambulances": 6,
        },
    ])

    results = st.session_state.get("simulation_results")

    if not results:
        st.warning("No simulation data found. Run Disaster Input first.")
        st.stop()

    allocation = results.get("allocation_result", {})
    scenario = allocation.get("scenario", {})

    raw_ambulances = scenario.get("ambulances", [])

    if not raw_ambulances:
        st.warning("No ambulance data found in simulation output.")
        st.stop()

    base_ambulances = pd.DataFrame(raw_ambulances)
    assignments = results.get("allocation_result", {}) \
                        .get("solvers", {}) \
                        .get("classical-optimal-flow", {}) \
                        .get("assignments", [])
    
    ambulance_to_hospital = {
        a["ambulance_id"]: a.get("hospital_id")
        for a in assignments
    }

    base_ambulances["Assigned Hospital"] = base_ambulances["id"].map(ambulance_to_hospital)

    ambulances = cached_ambulance_sim(base_ambulances, tick, updated_time)
    hospitals = cached_hospital_sim(base_hospitals, ambulances, tick)

    ambulances["Assigned Hospital"] = ambulances["id"].map(ambulance_to_hospital)

    results = st.session_state.get("simulation_results", {})
    if not results:
        st.warning("No simulation data found. Run Disaster Input first.")
        st.stop()
    allocation = results.get("allocation_result", {})
    scenario = allocation.get("scenario", {})

    incidents = scenario.get("incidents", [])

    if not incidents:
        st.warning("No simulation data found. Run Disaster Input first.")
        return

    incident_labels = [
        f"{i.get('id')} - {i.get('severity_level', 'NA')}"
        for i in incidents
    ]

    selected_label = st.selectbox("Incident location", incident_labels)

    selected_incident = incidents[incident_labels.index(selected_label)]

    metrics = st.columns(4)
    metrics[0].metric("Priority", selected_incident.get("severity_level"))
    metrics[1].metric("Hospital Spaces", int(hospitals["Available Spaces"].sum()))
    metrics[2].metric("Ambulances Available", len(ambulances))
    metrics[3].metric("Updated", updated_time)

    tracker_map = folium.Map(
        location=[
            selected_incident.get("lat", 53.3811),
            selected_incident.get("lon", -1.4701),
        ],
        zoom_start=12,
        tiles="OpenStreetMap",
    )

    incidents = pd.DataFrame(scenario.get("incidents", []))
    ambulances = pd.DataFrame(raw_ambulances)

    # INCIDENTS
    for _, inc in incidents.iterrows():
        folium.Marker(
            location=[inc.get("lat", 0), inc.get("lon", 0)],
            popup=f"Incident {inc.get('id')} ({inc.get('severity_level')})",
            icon=folium.Icon(color="red", icon="warning-sign"),
        ).add_to(tracker_map)

    # AMBULANCES
    for _, amb in ambulances.iterrows():
        folium.Marker(
            location=[amb.get("lat", 0), amb.get("lon", 0)],
            popup=f"Ambulance {amb.get('id')}",
            icon=folium.Icon(color="blue", icon="plus-sign"),
        ).add_to(tracker_map)

    st_folium(tracker_map, width=1200, height=480, key=f"tracker_{tick}")

    st.subheader("Ambulances")

    render_table(pd.DataFrame(ambulances))

    st.subheader("Incidents")

    render_table(pd.DataFrame(incidents))


live_tracker()
