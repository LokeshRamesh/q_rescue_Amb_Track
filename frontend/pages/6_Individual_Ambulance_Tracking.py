import math
from datetime import datetime

import folium
import pandas as pd
import streamlit as st
from folium.plugins import AntPath
from streamlit_folium import st_folium

from ambulance_data import available_ambulance_count, build_ambulance_routes
from auth import require_login
from ui_theme import apply_global_style, page_header, render_table


st.set_page_config(
    page_title="Individual Ambulance Tracking",
    page_icon=":oncoming_automobile:",
    layout="wide",
)
apply_global_style()
require_login()

page_header("AT", "Individual Ambulance Tracking")

results = st.session_state.get("simulation_results", {})
allocation = results.get("allocation_result", {})
scenario = allocation.get("scenario", {})
solvers = allocation.get("solvers", {})
assignments = solvers.get("classical-optimal-flow", {}).get("assignments", [])

ambulances = {a["id"]: a for a in scenario.get("ambulances", [])}
incidents = {i["id"]: i for i in scenario.get("incidents", [])}

routes = []

for a in assignments:
    amb = ambulances.get(a["ambulance_id"])
    inc = incidents.get(a["incident_id"])

    if not amb or not inc:
        continue

    routes.append({
        "Ambulance ID": a["ambulance_id"],

        # 🚑 START = hospital/base location (you already have ambulances dataset)
        "Start Latitude": amb["lat"],
        "Start Longitude": amb["lon"],

        # 🚨 END = incident location
        "End Latitude": inc["lat"],
        "End Longitude": inc["lon"],

        "Start Location": "Hospital/Base",
        "Destination": f"Incident {a['incident_id']}",

        "Patient Priority": inc.get("severity_level", "NA"),
        "Base Speed": 40,
    })

routes_df = pd.DataFrame(routes)
selected_ambulance = st.selectbox("Select ambulance", routes_df["Ambulance ID"])

control_col1, control_col2 = st.columns(2)
with control_col1:
    live_refresh = st.toggle("Live refresh", value=True)
with control_col2:
    refresh_seconds = st.selectbox(
        "Refresh every",
        [3, 5, 10, 15],
        index=1,
        disabled=not live_refresh,
    )

if live_refresh:
    st.caption(f"Live tracking refreshes every {refresh_seconds} seconds.")
else:
    st.info("Live refresh is off. Turn it on to resume automatic tracking.")


def distance_km(start_lat, start_lon, end_lat, end_lon):
    earth_radius = 6371
    lat1 = math.radians(start_lat)
    lat2 = math.radians(end_lat)
    lat_delta = math.radians(end_lat - start_lat)
    lon_delta = math.radians(end_lon - start_lon)

    value = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(lon_delta / 2) ** 2
    )
    return earth_radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


@st.fragment(run_every=refresh_seconds if live_refresh else None)
def track_selected_ambulance():
    route = routes_df[routes_df["Ambulance ID"] == selected_ambulance].iloc[0]
    now = datetime.now()
    tick = int(now.timestamp() // refresh_seconds)

    speed_mph = route.get("Base Speed", 40)
    speed_kmh = speed_mph * 1.60934

    now = datetime.now()


    start_key = f"start_time_{selected_ambulance}"
    if start_key not in st.session_state:
        st.session_state[start_key] = now.timestamp()

    SIMULATION_TIME_SCALE = 0.1  

    elapsed_hours = (
        (now.timestamp() - st.session_state[start_key]) * SIMULATION_TIME_SCALE
    ) / 3600

    distance_travelled = speed_kmh * elapsed_hours

    total_distance = distance_km(
        route["Start Latitude"],
        route["Start Longitude"],
        route["End Latitude"],
        route["End Longitude"],
    )

    progress_ratio = min(distance_travelled / total_distance, 1.0)
    progress = int(progress_ratio * 100)

    current_latitude = route["Start Latitude"] + (
        route["End Latitude"] - route["Start Latitude"]
    ) * progress_ratio
    current_longitude = route["Start Longitude"] + (
        route["End Longitude"] - route["Start Longitude"]
    ) * progress_ratio

    speed = 0 if progress_ratio >= 1.0 else speed_mph
    total_distance = distance_km(
        route["Start Latitude"],
        route["Start Longitude"],
        route["End Latitude"],
        route["End Longitude"],
    )
    remaining_distance = total_distance * (1 - progress_ratio)
    eta_minutes = 0 if speed == 0 else max(1, round((remaining_distance / (speed * 1.60934)) * 60))
    status = "Arrived" if progress == 100 else "On Route"

    metric_columns = st.columns(5)
    metric_columns[0].metric("Ambulance", route["Ambulance ID"])
    metric_columns[1].metric("Status", status)
    metric_columns[2].metric("Speed", f"{speed} mph")
    metric_columns[3].metric("Progress", f"{progress}%")
    metric_columns[4].metric("ETA", f"{eta_minutes} min")

    st.progress(progress, text=f"{route['Start Location']} to {route['Destination']}")

    route_map = folium.Map(
        location=[
            (route["Start Latitude"] + route["End Latitude"]) / 2,
            (route["Start Longitude"] + route["End Longitude"]) / 2,
        ],
        zoom_start=13,
        tiles="OpenStreetMap",
    )

    route_points = [
        [route["Start Latitude"], route["Start Longitude"]],
        [current_latitude, current_longitude],
        [route["End Latitude"], route["End Longitude"]],
    ]

    AntPath(
        route_points,
        color="#ef232a",
        weight=5,
        delay=900,
        dash_array=[10, 18],
    ).add_to(route_map)

    folium.Marker(
        [route["Start Latitude"], route["Start Longitude"]],
        popup=f"Start: {route['Start Location']}",
        tooltip="Start",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(route_map)

    folium.Marker(
        [route["End Latitude"], route["End Longitude"]],
        popup=f"Destination: {route['Destination']}",
        tooltip="Destination",
        icon=folium.Icon(color="red", icon="plus-sign"),
    ).add_to(route_map)

    folium.Marker(
        [current_latitude, current_longitude],
        popup=(
            f"{route['Ambulance ID']}<br>"
            f"Speed: {speed} mph<br>"
            f"ETA: {eta_minutes} min"
        ),
        tooltip=route["Ambulance ID"],
        icon=folium.Icon(color="blue", icon="road"),
    ).add_to(route_map)

    st_folium(
        route_map,
        width=1200,
        height=520,
        key=f"individual_{selected_ambulance}_{tick}",
    )

    trip_details = pd.DataFrame(
        {
            "Ambulance": [route["Ambulance ID"]],
            "Start": [route["Start Location"]],
            "Destination": [route["Destination"]],
            "Priority": [route["Patient Priority"]],
            "Status": [status],
            "Speed": [f"{speed} mph"],
            "Progress": [f"{progress}%"],
            "ETA": [f"{eta_minutes} min"],
            "Updated": [now.strftime("%H:%M:%S")],
        }
    )
    render_table(trip_details)


track_selected_ambulance()
