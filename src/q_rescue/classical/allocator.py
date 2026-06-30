from q_rescue.domain.models import Ambulance, Assignment, Incident, OptimizationResult
from q_rescue.simulation.distance_matrix import DistanceMatrix, SeverityMapping


class GreedyAllocator:
    """Severity-first nearest-ambulance baseline for Member 4.

    The allocator now accepts a pre-computed ``DistanceMatrix`` and
    ``SeverityMapping`` from the simulation layer (Member 2), so it no
    longer computes distances directly from ``Location`` objects.
    """

    name = "classical-greedy"

    def solve(
        self,
        ambulances: list[Ambulance],
        incidents: list[Incident],
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> OptimizationResult:
        """Assign ambulances greedily: highest-severity incidents first,
        closest available ambulance wins.

        Args:
            ambulances:       Ambulance list from the scenario.
            incidents:        Incident list from the scenario.
            distance_matrix:  Raw distances (km) from ``build_distance_matrix()``.
            severity_mapping: Absolute severity weights from ``build_severity_mapping()``.

        Returns:
            An ``OptimizationResult`` with the greedy assignment.
        """
        available = {ambulance.id: ambulance for ambulance in ambulances}
        assignments: list[Assignment] = []

        # Sort incidents by severity weight descending (CRITICAL=100 first)
        sorted_incidents = sorted(incidents, key=lambda i: severity_mapping[i.id], reverse=True)

        for incident in sorted_incidents:
            if not available:
                break
            # Pick the nearest available ambulance using pre-computed distances
            ambulance = min(
                available.values(),
                key=lambda a: distance_matrix.matrix[a.id][incident.id],
            )
            distance = distance_matrix.matrix[ambulance.id][incident.id]
            assignments.append(Assignment(ambulance.id, incident.id, distance))
            del available[ambulance.id]

        return OptimizationResult(
            assignments=assignments,
            objective_value=sum(item.distance for item in assignments),
            solver_name=self.name,
        )


class OptimalAssignmentAllocator:
    """Min-cost-flow baseline for the current one-to-one assignment model."""

    name = "classical-optimal-flow"

    def __init__(
        self,
        distance_weight: float = 1.0,
        severity_weight: float = 8.0,
        critical_priority: bool = False,
    ) -> None:
        self.distance_weight = distance_weight
        self.severity_weight = severity_weight
        self.critical_priority = critical_priority

    def solve(
        self,
        ambulances: list[Ambulance],
        incidents: list[Incident],
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> OptimizationResult:
        target = min(len(ambulances), len(incidents))
        if target == 0:
            return OptimizationResult([], 0.0, self.name)

        flow = _MinCostFlow()
        source = "source"
        sink = "sink"

        for ambulance in ambulances:
            flow.add_edge(source, ambulance.id, capacity=1, cost=0.0)

        for incident in incidents:
            flow.add_edge(incident.id, sink, capacity=1, cost=0.0)

        edge_lookup: dict[tuple[str, str], _Edge] = {}
        for ambulance in ambulances:
            for incident in incidents:
                cost = self._assignment_cost(
                    ambulance.id,
                    incident.id,
                    distance_matrix,
                    severity_mapping,
                )
                edge_lookup[(ambulance.id, incident.id)] = flow.add_edge(
                    ambulance.id,
                    incident.id,
                    capacity=1,
                    cost=cost,
                )

        objective_value = flow.min_cost_flow(source, sink, target)
        assignments = [
            Assignment(
                ambulance_id=ambulance.id,
                incident_id=incident.id,
                distance=distance_matrix.matrix[ambulance.id][incident.id],
            )
            for ambulance in ambulances
            for incident in incidents
            if edge_lookup[(ambulance.id, incident.id)].flow == 1
        ]

        return OptimizationResult(
            assignments=assignments,
            objective_value=objective_value,
            solver_name=self.name,
            feasible=len(assignments) == target,
        )

    def _assignment_cost(
        self,
        ambulance_id: str,
        incident_id: str,
        distance_matrix: DistanceMatrix,
        severity_mapping: SeverityMapping,
    ) -> float:
        distance = distance_matrix.matrix[ambulance_id][incident_id]
        severity_normalised = severity_mapping[incident_id] / 100.0
        priority_bonus = (
            1_000_000.0 if self.critical_priority and severity_mapping[incident_id] == 100 else 0.0
        )
        return (
            self.distance_weight * distance
            - self.severity_weight * severity_normalised
            - priority_bonus
        )


class _Edge:
    def __init__(self, target: str, reverse_index: int, capacity: int, cost: float) -> None:
        self.target = target
        self.reverse_index = reverse_index
        self.capacity = capacity
        self.cost = cost
        self.flow = 0


class _MinCostFlow:
    def __init__(self) -> None:
        self.graph: dict[str, list[_Edge]] = {}

    def add_edge(self, source: str, target: str, capacity: int, cost: float) -> _Edge:
        forward = _Edge(target, len(self.graph.setdefault(target, [])), capacity, cost)
        backward = _Edge(source, len(self.graph.setdefault(source, [])), 0, -cost)
        self.graph[source].append(forward)
        self.graph[target].append(backward)
        return forward

    def min_cost_flow(self, source: str, sink: str, required_flow: int) -> float:
        total_cost = 0.0

        for _ in range(required_flow):
            distances, parents = self._shortest_path(source)
            if sink not in parents:
                raise ValueError("Unable to route the requested assignment flow")

            node = sink
            while node != source:
                previous, edge_index = parents[node]
                edge = self.graph[previous][edge_index]
                reverse = self.graph[edge.target][edge.reverse_index]
                edge.capacity -= 1
                edge.flow += 1
                reverse.capacity += 1
                reverse.flow -= 1
                total_cost += edge.cost
                node = previous

        return total_cost

    def _shortest_path(self, source: str) -> tuple[dict[str, float], dict[str, tuple[str, int]]]:
        distances = {node: float("inf") for node in self.graph}
        distances[source] = 0.0
        parents: dict[str, tuple[str, int]] = {}

        for _ in range(len(self.graph) - 1):
            updated = False
            for node, edges in self.graph.items():
                if distances[node] == float("inf"):
                    continue
                for index, edge in enumerate(edges):
                    if edge.capacity <= 0:
                        continue
                    candidate = distances[node] + edge.cost
                    if candidate < distances[edge.target]:
                        distances[edge.target] = candidate
                        parents[edge.target] = (node, index)
                        updated = True
            if not updated:
                break

        return distances, parents
