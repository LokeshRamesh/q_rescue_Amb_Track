from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from q_rescue.domain.models import (
    Ambulance,
    DisasterCategory,
    Hospital,
    Incident,
    Location,
    Severity,
)
from q_rescue.quantum.comparison import (
    ComparisonReport,
    SolverBenchmark,
    compare_solvers_with_inputs,
    load_benchmark_exports,
)
from q_rescue.quantum.qaoa_solver import MultiStartQAOASolver, QiskitQAOASolver, QuboSolver
from q_rescue.quantum.qubo import AmbulanceAllocationQuboBuilder
from q_rescue.simulation.distance_matrix import (
    DistanceMatrix,
    SeverityMapping,
    build_distance_matrix,
    build_severity_mapping,
)
from q_rescue.simulation.generator import DisasterScenario
from q_rescue.simulation.scenarios import generate_scenario_by_category
from q_rescue.simulation.sheffield import SHEFFIELD_HOSPITALS


DEFAULT_EXACT_VARIABLE_LIMIT = 24
DEFAULT_QAOA_VARIABLE_LIMIT = 24


@dataclass(frozen=True)
class AllocationSettings:
    """Runtime controls shared by UI requests and benchmark JSON generation."""

    distance_weight: float = 1.0
    severity_weight: float = 8.0
    constraint_penalty: float = 100.0
    critical_priority: bool = True
    run_exact: bool | None = None
    run_qaoa: bool = False
    exact_variable_limit: int = DEFAULT_EXACT_VARIABLE_LIMIT
    qaoa_variable_limit: int = DEFAULT_QAOA_VARIABLE_LIMIT
    qaoa_reps: int = 1
    qaoa_shots: int = 1024
    qaoa_maxiter: int = 100
    qaoa_attempts: int = 4
    seed: int = 42


def build_allocation_output_from_request(request: dict[str, Any]) -> dict[str, Any]:
    """Run the allocation workflow from a UI request and return UI-ready JSON data."""
    scenario = scenario_from_request(request)
    settings = settings_from_request(request)
    distance_matrix = build_distance_matrix(scenario)
    severity_mapping = build_severity_mapping(scenario)
    return build_allocation_output(
        scenario,
        distance_matrix,
        severity_mapping,
        settings=settings,
        request=request,
        source="ui_request",
    )


def build_allocation_output_from_benchmark(
    benchmark_dir: Path,
    *,
    settings: AllocationSettings | None = None,
) -> dict[str, Any]:
    """Run allocators against one of Member 2's exported benchmark directories."""
    scenario, distance_matrix, severity_mapping = load_benchmark_exports(benchmark_dir)
    return build_allocation_output(
        scenario,
        distance_matrix,
        severity_mapping,
        settings=settings or AllocationSettings(),
        request={"benchmark_dir": str(benchmark_dir)},
        source="benchmark_export",
    )


def build_allocation_output(
    scenario: DisasterScenario,
    distance_matrix: DistanceMatrix,
    severity_mapping: SeverityMapping,
    *,
    settings: AllocationSettings | None = None,
    request: dict[str, Any] | None = None,
    source: str = "generated",
) -> dict[str, Any]:
    """Run classical/quantum allocation comparisons and serialize the result."""
    settings = settings or AllocationSettings()
    binary_variables = len(scenario.ambulances) * len(scenario.incidents)
    run_exact, exact_skip_reason = _resolve_optional_solver(
        settings.run_exact,
        binary_variables=binary_variables,
        variable_limit=settings.exact_variable_limit,
        default_enabled=True,
        solver_label="exact enumeration",
    )
    run_qaoa, qaoa_skip_reason = _resolve_optional_solver(
        settings.run_qaoa,
        binary_variables=binary_variables,
        variable_limit=settings.qaoa_variable_limit,
        default_enabled=False,
        solver_label="QAOA",
    )

    builder = AmbulanceAllocationQuboBuilder(
        distance_weight=settings.distance_weight,
        severity_weight=settings.severity_weight,
        constraint_penalty=settings.constraint_penalty,
        critical_priority=settings.critical_priority,
    )
    report = compare_solvers_with_inputs(
        scenario,
        distance_matrix,
        severity_mapping,
        builder=builder,
        qaoa_solver=_build_qaoa_solver(settings),
        run_exact=run_exact,
        run_qaoa=run_qaoa,
    )
    return _report_to_payload(
        report,
        scenario,
        distance_matrix,
        severity_mapping,
        settings=settings,
        request=request or {},
        source=source,
        exact_skip_reason=exact_skip_reason,
        qaoa_skip_reason=qaoa_skip_reason,
    )


def scenario_from_request(request: dict[str, Any]) -> DisasterScenario:
    """Convert UI JSON into the internal ``DisasterScenario`` model.

    The request may contain explicit entity arrays or generation parameters.
    Explicit arrays are useful once the UI owns live incident/ambulance data;
    generation parameters are useful for deterministic demo simulations.
    """
    scenario_data = _first_mapping(request, "scenario", "disaster", "incident") or request
    category = _parse_category(scenario_data.get("category", request.get("category", "flood")))
    seed = int(scenario_data.get("seed", request.get("seed", 42)))

    ambulances_data = scenario_data.get("ambulances")
    incidents_data = scenario_data.get("incidents")
    if isinstance(ambulances_data, list) and isinstance(incidents_data, list):
        hospitals_data = scenario_data.get("hospitals")
        hospitals = (
            [_hospital_from_dict(item) for item in hospitals_data]
            if isinstance(hospitals_data, list)
            else list(SHEFFIELD_HOSPITALS)
        )
        return DisasterScenario(
            name=str(scenario_data.get("name", f"UI {category.value} scenario")),
            ambulances=[_ambulance_from_dict(item) for item in ambulances_data],
            incidents=[_incident_from_dict(item, category) for item in incidents_data],
            hospitals=hospitals,
            category=category,
        )

    ambulance_count = int(
        scenario_data.get(
            "ambulance_count",
            scenario_data.get("ambulances", scenario_data.get("ambulanceCount", 3)),
        )
    )
    incident_count = int(
        scenario_data.get(
            "incident_count",
            scenario_data.get("incidents", scenario_data.get("incidentCount", 5)),
        )
    )
    cluster_radius = float(scenario_data.get("cluster_radius_km", 1.0))
    config = {
        "simulation": {
            "ambulances": ambulance_count,
            "incidents": incident_count,
            "category": category.value,
            "cluster_radius_km": cluster_radius,
            "use_sheffield_coords": bool(scenario_data.get("use_sheffield_coords", True)),
        }
    }
    return generate_scenario_by_category(category, config=config, seed=seed)


def settings_from_request(request: dict[str, Any]) -> AllocationSettings:
    """Extract optimizer settings from UI JSON, preserving demo-safe defaults."""
    data = _first_mapping(request, "optimisation", "optimization", "settings") or {}
    scenario_data = _first_mapping(request, "scenario", "disaster", "incident") or {}
    seed = int(data.get("seed", scenario_data.get("seed", request.get("seed", 42))))
    return AllocationSettings(
        distance_weight=float(data.get("distance_weight", data.get("distanceWeight", 1.0))),
        severity_weight=float(data.get("severity_weight", data.get("severityWeight", 8.0))),
        constraint_penalty=float(
            data.get("constraint_penalty", data.get("constraintPenalty", 100.0))
        ),
        critical_priority=bool(data.get("critical_priority", data.get("criticalPriority", True))),
        run_exact=data.get("run_exact", data.get("runExact")),
        run_qaoa=bool(data.get("run_qaoa", data.get("runQaoa", False))),
        exact_variable_limit=int(data.get("exact_variable_limit", DEFAULT_EXACT_VARIABLE_LIMIT)),
        qaoa_variable_limit=int(data.get("qaoa_variable_limit", DEFAULT_QAOA_VARIABLE_LIMIT)),
        qaoa_reps=int(data.get("qaoa_reps", data.get("qaoaReps", 1))),
        qaoa_shots=int(data.get("qaoa_shots", data.get("qaoaShots", 1024))),
        qaoa_maxiter=int(data.get("qaoa_maxiter", data.get("qaoaMaxiter", 100))),
        qaoa_attempts=int(data.get("qaoa_attempts", data.get("qaoaAttempts", 4))),
        seed=seed,
    )


def write_json_output(payload: dict[str, Any], path: Path) -> None:
    """Write a UI allocation payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def _report_to_payload(
    report: ComparisonReport,
    scenario: DisasterScenario,
    distance_matrix: DistanceMatrix,
    severity_mapping: SeverityMapping,
    *,
    settings: AllocationSettings,
    request: dict[str, Any],
    source: str,
    exact_skip_reason: str | None,
    qaoa_skip_reason: str | None,
) -> dict[str, Any]:
    return {
        "source": source,
        "request": request,
        "scenario": _scenario_to_dict(scenario),
        "inputs": {
            "distance_matrix": distance_matrix.to_dict(),
            "severity_weights": severity_mapping,
        },
        "optimization": {
            "binary_variables": report.binary_variables,
            "settings": _settings_to_dict(settings),
            "gaps_from_exact": {
                "classical_greedy": report.classical_gap,
                "classical_optimal_flow": report.optimal_classical_gap,
                "qaoa": report.qaoa_gap,
                "classical_greedy_percent": report.classical_relative_gap_percent,
                "classical_optimal_flow_percent": report.optimal_classical_relative_gap_percent,
                "qaoa_percent": report.qaoa_relative_gap_percent,
            },
        },
        "solvers": {
            "classical-greedy": _benchmark_to_dict(report.classical),
            "classical-optimal-flow": _benchmark_to_dict(report.optimal_classical),
            "exact-enumeration": _optional_benchmark_to_dict(
                report.exact, "exact-enumeration", exact_skip_reason
            ),
            "qiskit-qaoa": _optional_benchmark_to_dict(
                report.qaoa, "qiskit-qaoa", qaoa_skip_reason
            ),
        },
    }


def _scenario_to_dict(scenario: DisasterScenario) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "category": scenario.category.value,
        "counts": {
            "ambulances": len(scenario.ambulances),
            "incidents": len(scenario.incidents),
            "hospitals": len(scenario.hospitals),
        },
        "ambulances": [
            {
                "id": ambulance.id,
                "lat": round(ambulance.location.x, 6),
                "lon": round(ambulance.location.y, 6),
                "status": ambulance.status,
            }
            for ambulance in scenario.ambulances
        ],
        "incidents": [
            {
                "id": incident.id,
                "lat": round(incident.location.x, 6),
                "lon": round(incident.location.y, 6),
                "severity_level": incident.severity.name,
                "severity_weight": incident.severity.absolute_weight(),
                "category": incident.category.value,
            }
            for incident in scenario.incidents
        ],
        "hospitals": [
            {
                "id": hospital.id,
                "name": hospital.name,
                "lat": round(hospital.location.x, 6),
                "lon": round(hospital.location.y, 6),
                "capacity": hospital.capacity,
                "available_beds": hospital.available_beds,
            }
            for hospital in scenario.hospitals
        ],
    }


def _benchmark_to_dict(benchmark: SolverBenchmark) -> dict[str, Any]:
    return {
        "status": "ok",
        "solver_name": benchmark.solver_name,
        "qubo_energy": benchmark.qubo_energy,
        "runtime_seconds": benchmark.runtime_seconds,
        "feasible": benchmark.feasible,
        "metrics": benchmark.metrics,
        "assignments": [
            {
                "ambulance_id": assignment.ambulance_id,
                "incident_id": assignment.incident_id,
                "distance_km": assignment.distance,
                "hospital_id": assignment.hospital_id,
            }
            for assignment in benchmark.assignments
        ],
    }


def _optional_benchmark_to_dict(
    benchmark: SolverBenchmark | None,
    solver_name: str,
    skip_reason: str | None,
) -> dict[str, Any]:
    if benchmark is not None:
        return _benchmark_to_dict(benchmark)
    return {"status": "skipped", "solver_name": solver_name, "reason": skip_reason}


def _settings_to_dict(settings: AllocationSettings) -> dict[str, Any]:
    return {
        "distance_weight": settings.distance_weight,
        "severity_weight": settings.severity_weight,
        "constraint_penalty": settings.constraint_penalty,
        "critical_priority": settings.critical_priority,
        "run_exact": settings.run_exact,
        "run_qaoa": settings.run_qaoa,
        "exact_variable_limit": settings.exact_variable_limit,
        "qaoa_variable_limit": settings.qaoa_variable_limit,
        "qaoa_reps": settings.qaoa_reps,
        "qaoa_shots": settings.qaoa_shots,
        "qaoa_maxiter": settings.qaoa_maxiter,
        "qaoa_attempts": settings.qaoa_attempts,
        "seed": settings.seed,
    }


def _resolve_optional_solver(
    requested: bool | None,
    *,
    binary_variables: int,
    variable_limit: int,
    default_enabled: bool,
    solver_label: str,
) -> tuple[bool, str | None]:
    enabled = default_enabled if requested is None else bool(requested)
    if not enabled:
        return False, f"{solver_label} disabled for this run"
    if binary_variables > variable_limit:
        return (
            False,
            f"{solver_label} skipped because {binary_variables} binary variables exceed "
            f"the configured limit of {variable_limit}",
        )
    return True, None


def _build_qaoa_solver(settings: AllocationSettings) -> QuboSolver:
    if settings.qaoa_attempts == 1:
        return QiskitQAOASolver(
            reps=settings.qaoa_reps,
            shots=settings.qaoa_shots,
            seed=settings.seed,
            maxiter=settings.qaoa_maxiter,
        )
    return MultiStartQAOASolver(
        reps=settings.qaoa_reps,
        shots=settings.qaoa_shots,
        seed=settings.seed,
        maxiter=settings.qaoa_maxiter,
        attempts=settings.qaoa_attempts,
    )


def _first_mapping(data: dict[str, Any], *keys: str) -> dict[str, Any] | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, dict):
            return value
    return None


def _ambulance_from_dict(data: dict[str, Any]) -> Ambulance:
    return Ambulance(
        id=str(data["id"]),
        location=_location_from_dict(data),
        status=str(data.get("status", "Available")).capitalize(),
    )


def _incident_from_dict(data: dict[str, Any], default_category: DisasterCategory) -> Incident:
    return Incident(
        id=str(data["id"]),
        location=_location_from_dict(data),
        severity=_parse_severity(data),
        category=_parse_category(data.get("category", default_category.value)),
    )


def _hospital_from_dict(data: dict[str, Any]) -> Hospital:
    return Hospital(
        id=str(data["id"]),
        name=str(data.get("name", data["id"])),
        location=_location_from_dict(data),
        capacity=int(data.get("capacity", 0)),
        available_beds=int(data.get("available_beds", data.get("availableBeds", 0))),
    )


def _location_from_dict(data: dict[str, Any]) -> Location:
    if "location" in data and isinstance(data["location"], dict):
        data = data["location"]
    return Location(
        x=float(data.get("lat", data.get("x"))),
        y=float(data.get("lon", data.get("lng", data.get("y")))),
    )


def _parse_category(value: object) -> DisasterCategory:
    if isinstance(value, DisasterCategory):
        return value
    text = str(value).lower()
    for category in DisasterCategory:
        if text in {category.value, category.name.lower()}:
            return category
    raise ValueError(f"Unknown disaster category: {value!r}")


def _parse_severity(data: dict[str, Any]) -> Severity:
    value = data.get("severity", data.get("severity_level", data.get("severityLevel")))
    if value is None:
        value = data.get("severity_weight", data.get("severityWeight", Severity.MEDIUM.value))
    if isinstance(value, int):
        if value in {25, 50, 75, 100}:
            return {
                25: Severity.LOW,
                50: Severity.MEDIUM,
                75: Severity.HIGH,
                100: Severity.CRITICAL,
            }[value]
        return Severity(value)
    text = str(value).upper()
    if text.isdigit():
        return _parse_severity({"severity": int(text)})
    return Severity[text]
