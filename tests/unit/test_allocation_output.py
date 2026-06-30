from __future__ import annotations

from q_rescue.services.allocation_output import (
    AllocationSettings,
    build_allocation_output,
    build_allocation_output_from_request,
    scenario_from_request,
)
from q_rescue.simulation.distance_matrix import build_distance_matrix, build_severity_mapping


def test_ui_request_generates_allocation_json_result() -> None:
    request = {
        "scenario": {
            "category": "flood",
            "ambulances": 2,
            "incidents": 3,
            "seed": 42,
        },
        "optimisation": {
            "critical_priority": True,
            "run_exact": True,
            "run_qaoa": False,
        },
    }

    allocation_result = build_allocation_output_from_request(request)

    assert allocation_result["source"] == "ui_request"
    assert allocation_result["scenario"]["category"] == "flood"
    assert allocation_result["scenario"]["counts"] == {
        "ambulances": 2,
        "incidents": 3,
        "hospitals": 4,
    }
    assert allocation_result["optimization"]["binary_variables"] == 6
    assert allocation_result["solvers"]["classical-greedy"]["status"] == "ok"
    assert allocation_result["solvers"]["classical-optimal-flow"]["status"] == "ok"
    assert allocation_result["solvers"]["exact-enumeration"]["status"] == "ok"
    assert allocation_result["solvers"]["qiskit-qaoa"]["status"] == "skipped"
    assert len(allocation_result["solvers"]["classical-greedy"]["assignments"]) == 2


def test_ui_request_can_use_explicit_member_two_style_entities() -> None:
    request = {
        "disaster": {
            "name": "UI supplied flood",
            "category": "flood",
            "ambulances": [
                {"id": "A1", "lat": 53.3811, "lon": -1.4701, "status": "available"},
                {"id": "A2", "lat": 53.4096, "lon": -1.4565, "status": "available"},
            ],
            "incidents": [
                {
                    "id": "I1",
                    "lat": 53.4,
                    "lon": -1.47,
                    "severity_level": "CRITICAL",
                }
            ],
        }
    }

    scenario = scenario_from_request(request)

    assert scenario.name == "UI supplied flood"
    assert len(scenario.ambulances) == 2
    assert len(scenario.incidents) == 1
    assert scenario.incidents[0].severity.name == "CRITICAL"
    assert len(scenario.hospitals) == 4


def test_large_result_marks_exact_and_qaoa_as_skipped() -> None:
    scenario = scenario_from_request(
        {
            "scenario": {
                "category": "flood",
                "ambulances": 5,
                "incidents": 6,
                "seed": 42,
            }
        }
    )

    allocation_result = build_allocation_output(
        scenario,
        build_distance_matrix(scenario),
        build_severity_mapping(scenario),
        settings=AllocationSettings(run_exact=True, run_qaoa=True),
    )

    assert allocation_result["optimization"]["binary_variables"] == 30
    assert allocation_result["solvers"]["exact-enumeration"]["status"] == "skipped"
    assert allocation_result["solvers"]["qiskit-qaoa"]["status"] == "skipped"
