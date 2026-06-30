import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from auth import require_login
from ui_theme import apply_global_style, page_header, render_table


st.set_page_config(page_title="Comparison View", page_icon=":balance_scale:", layout="wide")
apply_global_style()
require_login()

page_header("QO", "Optimisation Comparison")

results = st.session_state["simulation_results"]
allocation = results.get("allocation_result", {})
solvers = allocation.get("solvers", {})

def extract_metrics(solver):
    m = solver.get("metrics", {})
    return {
        "Response Time": m.get("average_distance_km", 0),
        "Fuel Usage": 0,
        "Resource Utilisation": m.get("coverage_percent", 0),
        "Route Efficiency": m.get("coverage_percent", 0),
        "Allocation Accuracy": m.get("critical_coverage_percent", 0),
    }

classical = solvers.get("classical-optimal-flow", {})
quantum = solvers.get("qiskit-qaoa", {})

if quantum.get("status") == "ok":
    quantum_metrics = extract_metrics(quantum)
    quantum_exists = True
else:
    quantum_metrics = None
    quantum_exists = False

    if quantum.get("status") == "skipped":
        st.warning(f"Quantum skipped: {quantum.get('reason', 'Unknown reason')}")

classical_metrics = extract_metrics(classical)

data = {
    "Metric": [
        "Response Time",
        "Fuel Usage",
        "Resource Utilisation",
        "Route Efficiency",
        "Allocation Accuracy",
    ],
    "Classical": list(classical_metrics.values()),
}

if quantum_metrics:
    data["Quantum"] = list(quantum_metrics.values())

comparison = pd.DataFrame(data)

comparison["Classical"] = pd.to_numeric(comparison["Classical"], errors="coerce").fillna(0)

if quantum_exists:
    comparison["Quantum"] = pd.to_numeric(comparison["Quantum"], errors="coerce").fillna(0)

render_table(comparison)

profile = comparison.copy()
profile["Classical"] = profile["Classical"].astype(float)

if quantum_exists:
    profile["Quantum"] = profile["Quantum"].astype(float)

methods = ["Classical"]
if "Quantum" in profile.columns:
    methods.append("Quantum")

if "Quantum" in profile.columns:
    profile[["Quantum"]] = profile[["Quantum"]].astype(float)

for metric in ["Response Time", "Fuel Usage"]:
    row = profile["Metric"] == metric

    best_value = profile.loc[row, methods].min(axis=1)

    profile.loc[row, "Classical"] = (
        best_value / profile.loc[row, "Classical"] * 100
    )

    if "Quantum" in methods:
        profile.loc[row, "Quantum"] = (
            best_value / profile.loc[row, "Quantum"] * 100
        )

for metric in ["Resource Utilisation", "Route Efficiency", "Allocation Accuracy"]:
    row = profile["Metric"] == metric

    best_value = profile.loc[row, methods].max(axis=1)

    profile.loc[row, "Classical"] = (
        profile.loc[row, "Classical"] / best_value * 100
    )

    if "Quantum" in methods:
        profile.loc[row, "Quantum"] = (
            profile.loc[row, "Quantum"] / best_value * 100
        )

radar_chart = go.Figure()

radar_chart.add_trace(
    go.Scatterpolar(
        r=profile["Classical"],
        theta=profile["Metric"],
        fill="toself",
        name="Classical",
        line=dict(color="#ef232a", width=3),
        fillcolor="rgba(239, 35, 42, 0.24)",
        hovertemplate="Classical<br>%{theta}: %{r:.1f}%<extra></extra>",
    )
)

if "Quantum" in profile.columns:
    radar_chart.add_trace(
        go.Scatterpolar(
            r=profile["Quantum"],
            theta=profile["Metric"],
            fill="toself",
            name="Quantum",
            line=dict(color="#f2f2f2", width=3),
            fillcolor="rgba(242, 242, 242, 0.14)",
            hovertemplate="Quantum<br>%{theta}: %{r:.1f}%<extra></extra>",
        )
    )

radar_chart.update_layout(
    title="Performance Profile (Higher Is Better)",
    paper_bgcolor="#221f27",
    plot_bgcolor="#221f27",
    font_color="#ffffff",
    polar=dict(
        bgcolor="#221f27",
        radialaxis=dict(
            visible=True,
            range=[0, 105],
            ticksuffix="%",
            gridcolor="rgba(255, 255, 255, 0.18)",
        ),
        angularaxis=dict(gridcolor="rgba(255, 255, 255, 0.18)"),
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.5),
    margin=dict(l=60, r=60, t=100, b=50),
)

st.plotly_chart(radar_chart, use_container_width=True)


y_cols = ["Classical"]
if "Quantum" in comparison.columns:
    y_cols.append("Quantum")
bar_chart = px.bar(
    comparison,
    x="Metric",
    y=y_cols,
    barmode="group",
    title="Classical vs Quantum",
    color_discrete_sequence=["#ef232a", "#f2f2f2"],
)
bar_chart.update_layout(
    plot_bgcolor="#221f27",
    paper_bgcolor="#221f27",
    font_color="#ffffff",
)

scores = {
    "Method": ["Classical"],
    "Score": [comparison["Classical"].sum()],
}

if quantum_exists and "Quantum" in comparison.columns:
    scores["Method"].append("Quantum")
    scores["Score"].append(comparison["Quantum"].sum())

totals = pd.DataFrame(scores)
pie_chart = px.pie(
    totals,
    names="Method",
    values="Score",
    title="Overall Performance",
    color_discrete_sequence=["#ef232a", "#f2f2f2"],
)
pie_chart.update_layout(
    paper_bgcolor="#221f27",
    font_color="#ffffff",
)

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(bar_chart, use_container_width=True)
with chart_col2:
    st.plotly_chart(pie_chart, use_container_width=True)

st.subheader("Solver Breakdown")

rows = []

for name, data in solvers.items():
    if not isinstance(data, dict):
        continue

    metrics = data.get("metrics", {})
    status = data.get("status", "ok")

    rows.append({
        "Solver": name,
        "Status": status,
        "Average Distance": metrics.get("average_distance_km"),
        "Coverage %": metrics.get("coverage_percent"),
        "Critical Coverage %": metrics.get("critical_coverage_percent"),
    })

df = pd.DataFrame(rows)

render_table(df)