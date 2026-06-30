import pandas as pd
import streamlit as st

from adapters import ambulance_from_route


ROUTE_TEMPLATES = [
    {
        "start": "Meadowhall",
        "destination": "Northern General Hospital",
        "start_latitude": 53.4148,
        "start_longitude": -1.4103,
        "end_latitude": 53.4109,
        "end_longitude": -1.4587,
        "priority": "Critical",
        "speed": 38,
    },
    {
        "start": "Hillsborough",
        "destination": "Royal Hallamshire Hospital",
        "start_latitude": 53.4021,
        "start_longitude": -1.5002,
        "end_latitude": 53.3785,
        "end_longitude": -1.4939,
        "priority": "High",
        "speed": 34,
    },
    {
        "start": "Darnall",
        "destination": "Northern General Hospital",
        "start_latitude": 53.3845,
        "start_longitude": -1.4135,
        "end_latitude": 53.4109,
        "end_longitude": -1.4587,
        "priority": "Medium",
        "speed": 31,
    },
    {
        "start": "Ecclesall Road",
        "destination": "Royal Hallamshire Hospital",
        "start_latitude": 53.3704,
        "start_longitude": -1.4978,
        "end_latitude": 53.3785,
        "end_longitude": -1.4939,
        "priority": "Critical",
        "speed": 40,
    },
    {
        "start": "Attercliffe",
        "destination": "Sheffield Children's Hospital",
        "start_latitude": 53.3950,
        "start_longitude": -1.4330,
        "end_latitude": 53.3817,
        "end_longitude": -1.4906,
        "priority": "High",
        "speed": 35,
    },
    {
        "start": "Sheffield City Centre",
        "destination": "Claremont Hospital",
        "start_latitude": 53.3811,
        "start_longitude": -1.4701,
        "end_latitude": 53.3682,
        "end_longitude": -1.5154,
        "priority": "Medium",
        "speed": 29,
    },
]


def available_ambulance_count():
    simulation = st.session_state.get("simulation_results", {})
    return max(0, int(simulation.get("available_ambulances", 6)))


def build_ambulance_routes(count):
    rows = []

    for index in range(count):
        template = ROUTE_TEMPLATES[index % len(ROUTE_TEMPLATES)]
        offset_group = index // len(ROUTE_TEMPLATES)
        coordinate_offset = offset_group * 0.00035

        rows.append(
            {
                "Ambulance ID": f"AMB-{index + 1:02d}",
                "Start Location": template["start"],
                "Destination": template["destination"],
                "Start Latitude": template["start_latitude"] + coordinate_offset,
                "Start Longitude": template["start_longitude"] - coordinate_offset,
                "End Latitude": template["end_latitude"],
                "End Longitude": template["end_longitude"],
                "Patient Priority": template["priority"],
                "Base Speed": template["speed"],
            }
        )

    routes = pd.DataFrame(rows)
    routes.attrs["domain_ambulances"] = [ambulance_from_route(row) for row in rows]
    return routes
