# Team Data Interfaces & Contracts

This document defines the stable data structures and expected formats shared between the simulation module (Member 2), quantum solver (Member 1), classical solver (Member 4), and dashboard (Member 3).

---

## 1. Internal API Contracts (Python)

When integrating code within the `q_rescue` package, use the typed Python models directly. Do not pass JSON dictionaries or raw CSV paths between modules.

### Simulation → Solvers

The scenario generator (`q_rescue.simulation.scenarios`) outputs a `DisasterScenario` dataclass.

**Member 1 (Quantum):** Consumes `DisasterScenario`, `DistanceMatrix`, and
`SeverityMapping` via `AmbulanceAllocationQuboBuilder.build()`.
**Member 4 (Classical):** Consumes `scenario.ambulances` and `scenario.incidents` via `GreedyAllocator.solve()`.

### Solvers → Dashboard / Metrics

All solvers must return an `OptimizationResult` containing:
- `assignments: list[Assignment]`
- `objective_value: float`
- `solver_name: str`
- `feasible: bool`

**Member 3 (Dashboard):** Uses `q_rescue.services.response_service.compare_allocators()` which accepts a `DisasterScenario` and returns the metrics and `OptimizationResult` for both solvers.

For the hackathon UI, use `q_rescue.services.allocation_output` when the
dashboard needs one JSON result containing both the simulated scenario and the
allocation results. This accepts either a UI request with disaster parameters or
explicit ambulance/incident/hospital arrays.

---

## 2. External Exports (CSV & JSON)

For downstream analysis, debugging, or external tools, the simulation module exports raw datasets to `data/outputs/`.

### JSON Exports

#### `scenario.json`
Contains all entities, categories, and severity mappings in a single file. Useful for web dashboards.

#### `distance_matrix.json`
Nested dictionary of raw travel distances:
`{"ambulance_id": {"incident_id": distance_km}}`.

#### `severity_weights.json`
Flat dictionary of incident priority weights:
`{"incident_id": severity_weight}`.

#### `allocation_results.json`
UI-ready allocation output produced by:

```bash
.venv/bin/python scripts/generate_allocation_outputs.py
```

The result includes:
- `scenario`: category, entity counts, ambulances, incidents, and hospitals
- `inputs`: raw `distance_matrix` and `severity_weights`
- `optimization`: binary variable count, QUBO settings, and gaps from exact
- `solvers`: assignment lists and stats for `classical-greedy`,
  `classical-optimal-flow`, `exact-enumeration`, and `qiskit-qaoa`

The UI can also submit a single request:

```json
{
  "scenario": {
    "category": "flood",
    "ambulances": 10,
    "incidents": 20,
    "seed": 42
  },
  "optimisation": {
    "critical_priority": true,
    "run_qaoa": false
  }
}
```

and generate output with:

```bash
.venv/bin/python scripts/generate_allocation_outputs.py \
  --request-json data/outputs/ui_request.json \
  --output data/outputs/allocation_results.json
```

### CSV Exports

#### `ambulances.csv`
| id | lat | lon | status |
|---|---|---|---|
| A1 | 53.3851 | -1.4590 | Available |

#### `incidents.csv`
| id | lat | lon | severity_level | severity_weight | category |
|---|---|---|---|---|---|
| I1 | 53.4004 | -1.4754 | CRITICAL | 100 | flood |

#### `hospitals.csv`
| id | name | lat | lon | capacity | available_beds |
|---|---|---|---|---|---|
| H1 | Northern General Hospital | 53.4096 | -1.4565 | 1100 | 770 |

#### `distance_matrix.csv`
Rows = ambulances, Columns = incidents. Values = raw distance in kilometres.

| ambulance_id | I1 | I2 | I3 |
|---|---|---|---|
| A1 | 2.61 | 10.85 | 4.23 |

#### `severity_weights.csv`
Rows = incidents. Values = absolute priority weights.

| incident_id | severity_weight |
|---|---:|
| I1 | 100 |
