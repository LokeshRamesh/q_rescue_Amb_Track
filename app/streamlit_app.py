import streamlit as st

from q_rescue.services.response_service import compare_allocators
from q_rescue.simulation.generator import generate_scenario


st.set_page_config(page_title="Q-Rescue AI", layout="wide")
st.title("Q-Rescue AI")
st.caption("Classical and quantum-inspired emergency resource allocation")

seed = st.sidebar.number_input("Scenario seed", min_value=0, value=42)
ambulance_count = st.sidebar.slider("Ambulances", 1, 10, 3)
incident_count = st.sidebar.slider("Incidents", 1, 20, 5)

scenario = generate_scenario(ambulance_count, incident_count, seed=int(seed))
if ambulance_count * incident_count > 24:
    st.warning(
        "The starter exact QUBO solver supports at most 24 binary variables. "
        "Reduce ambulances x incidents, or connect Member 1's Qiskit QAOA solver."
    )
    st.stop()
comparison = compare_allocators(scenario)

for column, (name, payload) in zip(st.columns(2), comparison.items(), strict=True):
    with column:
        result = payload["result"]
        st.subheader(name.title())
        st.metric("Objective", f"{result.objective_value:.2f}")
        st.json(payload["metrics"])
        st.dataframe([assignment.__dict__ for assignment in result.assignments])
