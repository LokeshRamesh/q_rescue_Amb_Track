from q_rescue.classical.allocator import GreedyAllocator, OptimalAssignmentAllocator
from q_rescue.domain.models import Ambulance, Incident, Location, Severity
from q_rescue.simulation.distance_matrix import DistanceMatrix


def test_optimal_allocator_beats_greedy_local_choice() -> None:
    ambulances = [
        Ambulance("A1", Location(0.0, 0.0)),
        Ambulance("A2", Location(0.0, 0.0)),
    ]
    incidents = [
        Incident("I-critical", Location(0.0, 0.0), Severity.CRITICAL),
        Incident("I-high", Location(0.0, 0.0), Severity.HIGH),
    ]
    distance_matrix = DistanceMatrix(
        matrix={
            "A1": {"I-critical": 1.0, "I-high": 2.0},
            "A2": {"I-critical": 1.1, "I-high": 100.0},
        },
        ambulance_ids=["A1", "A2"],
        incident_ids=["I-critical", "I-high"],
    )
    severity_mapping = {"I-critical": 100, "I-high": 75}

    greedy = GreedyAllocator().solve(ambulances, incidents, distance_matrix, severity_mapping)
    optimal = OptimalAssignmentAllocator().solve(
        ambulances,
        incidents,
        distance_matrix,
        severity_mapping,
    )

    assert [(a.ambulance_id, a.incident_id) for a in greedy.assignments] == [
        ("A1", "I-critical"),
        ("A2", "I-high"),
    ]
    assert [(a.ambulance_id, a.incident_id) for a in optimal.assignments] == [
        ("A1", "I-high"),
        ("A2", "I-critical"),
    ]
    greedy_objective = sum(
        distance_matrix.matrix[assignment.ambulance_id][assignment.incident_id]
        - 8.0 * severity_mapping[assignment.incident_id] / 100.0
        for assignment in greedy.assignments
    )
    assert optimal.objective_value < greedy_objective


def test_optimal_allocator_default_severity_weight_matches_project_config() -> None:
    allocator = OptimalAssignmentAllocator()

    assert allocator.severity_weight == 8.0


def test_optimal_allocator_hard_critical_priority_overrides_distance_tradeoff() -> None:
    ambulances = [Ambulance("A1", Location(0.0, 0.0))]
    incidents = [
        Incident("I-low", Location(0.0, 0.0), Severity.LOW),
        Incident("I-critical", Location(0.0, 0.0), Severity.CRITICAL),
    ]
    distance_matrix = DistanceMatrix(
        matrix={"A1": {"I-low": 1.0, "I-critical": 100.0}},
        ambulance_ids=["A1"],
        incident_ids=["I-low", "I-critical"],
    )
    severity_mapping = {"I-low": 25, "I-critical": 100}

    soft = OptimalAssignmentAllocator().solve(
        ambulances,
        incidents,
        distance_matrix,
        severity_mapping,
    )
    hard = OptimalAssignmentAllocator(critical_priority=True).solve(
        ambulances,
        incidents,
        distance_matrix,
        severity_mapping,
    )

    assert soft.assignments[0].incident_id == "I-low"
    assert hard.assignments[0].incident_id == "I-critical"


def test_optimal_allocator_returns_empty_result_for_empty_inputs() -> None:
    result = OptimalAssignmentAllocator().solve([], [], DistanceMatrix(), {})

    assert result.assignments == []
    assert result.objective_value == 0.0
    assert result.feasible
