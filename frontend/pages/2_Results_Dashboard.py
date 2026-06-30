import pandas as pd
import streamlit as st

from auth import require_login
from ui_theme import apply_global_style, page_header, render_table


st.set_page_config(page_title="Results Dashboard", page_icon=":bar_chart:", layout="wide")
apply_global_style()
require_login()

page_header("RS", "Simulation Results")

if "simulation_results" not in st.session_state:
    st.warning("Run a simulation from Disaster Input first.")
    st.stop()

results = st.session_state["simulation_results"]

allocation = results.get("allocation_result", {})
scenario = allocation.get("scenario", {})
optimization = allocation.get("optimization", {})
solvers = allocation.get("solvers", {})

primary = solvers.get("classical-optimal-flow", {})
metrics = primary.get("metrics", {})

summary = pd.DataFrame(
    {
        "Result": [
            "Disaster Type",
            "Location",
            "Severity",
            "Affected Population",
            "Average Distance (km)",
            "Coverage %",
            "Critical Coverage %",
        ],
        "Value": [
            scenario.get("category"),
            results.get("location"),
            results.get("severity"),
            f'{results.get("affected_population", 0):,}',
            metrics.get("average_distance_km", 0),
            metrics.get("coverage_percent", 0),
            metrics.get("critical_coverage_percent", 0),
        ],
    }
)

resources = pd.DataFrame(
    {
        "Resource": ["Ambulances", "Rescue Teams", "Food Units"],
        "Available": [
            scenario.get("counts", {}).get("ambulances"),
            results.get("available_rescue_teams"),
            results.get("available_food_units"),
        ]
    }
)

risk = pd.DataFrame(
    {
        "Risk Level": ["Low", "Medium", "High", "Critical"],
        "Percentage": [25, 25, 25, 25],
    }
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Summary")
    render_table(summary)
with col2:
    st.subheader("Resources")
    render_table(resources)

st.subheader("Risk")
render_table(risk)
