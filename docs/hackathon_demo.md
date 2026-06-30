# Q-Rescue Hackathon Demo Plan

This document is the short presentation-ready version of Member 1's progress.
Use `docs/quantum-methodology.md` for the full technical record.

## Core Story

Q-Rescue AI turns emergency ambulance allocation into an optimisation problem.
Member 1's contribution is the QUBO and quantum workflow:

1. Encode ambulance-to-incident choices as binary variables.
2. Add QUBO penalties so invalid assignments are expensive.
3. Run exact enumeration on small cases to validate correctness.
4. Run Qiskit QAOA on small cases to prove the quantum workflow works.
5. Add multi-start QAOA because single-start QAOA was seed-sensitive.
6. Add scalable benchmark mode for medium and large scenarios.
7. Add a stronger optimal-flow classical baseline beyond greedy.
8. Add severity tuning and optional hard critical-priority mode.

## What We Can Claim

- The QUBO formulation works and is tested.
- The Qiskit QAOA path runs end-to-end on the small benchmark.
- Multi-start QAOA improves seed-sensitive small-case results.
- Exact enumeration is useful only for small validation cases.
- Local statevector QAOA is not scalable to 200 or 2000 binary variables.
- Medium and large benchmarks can still be evaluated honestly with exact/QAOA
  marked `N/A`.
- Hard critical priority can enforce 100% critical coverage in tested medium
  and large scenarios.

## What We Cannot Claim Yet

- We cannot claim quantum advantage.
- We cannot claim local QAOA is faster than classical methods.
- We cannot claim medium/large QAOA results until we use a more scalable
  simulator, decomposition method, quantum-inspired heuristic, or real backend.

## Final Results Table

| Scenario | Binary variables | Mode | Solver | QUBO energy | Avg distance | Coverage | Critical coverage | Feasible |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- |
| Small Sheffield flood | 15 | Default weights | Exact enumeration | -2.467636 | 4.511 km | 60.0% | 100.0% | Yes |
| Small Sheffield flood | 15 | Default weights | Multi-start QAOA | -1.915805 | 4.028 km | 60.0% | 100.0% | Yes |
| Medium Sheffield flood | 200 | Safe mode | Greedy | -3.359378 | 5.864 km | 50.0% | 100.0% | Yes |
| Medium Sheffield flood | 200 | Safe mode | Optimal flow | -24.889142 | 2.511 km | 50.0% | 0.0% | Yes |
| Medium Sheffield flood | 200 | Hard critical priority | Optimal flow | -24.494510 | 2.751 km | 50.0% | 100.0% | Yes |
| Large Sheffield city-wide | 2000 | Safe mode | Greedy | -61.157556 | 4.742 km | 20.0% | 100.0% | Yes |
| Large Sheffield city-wide | 2000 | Safe mode | Optimal flow | -108.610696 | 1.869 km | 20.0% | 72.2% | Yes |
| Large Sheffield city-wide | 2000 | Hard critical priority | Optimal flow | -88.243889 | 3.388 km | 20.0% | 100.0% | Yes |

## Reproducible Commands

Install dependencies:

```bash
pip install -e ".[quantum,dev]"
```

Run tests:

```bash
.venv/bin/python -m pytest
```

Small benchmark with exact and QAOA:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/small \
  --reps 1 \
  --shots 2048 \
  --maxiter 50 \
  --seed 42 \
  --qaoa-attempts 4
```

Medium benchmark, safe mode:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/medium \
  --skip-exact \
  --skip-qaoa
```

Large benchmark, safe mode:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/large \
  --skip-exact \
  --skip-qaoa
```

Medium benchmark with hard critical priority:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/medium \
  --skip-exact \
  --skip-qaoa \
  --critical-priority
```

Large benchmark with hard critical priority:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/large \
  --skip-exact \
  --skip-qaoa \
  --critical-priority
```

Severity sensitivity example:

```bash
.venv/bin/python scripts/compare_solvers.py \
  --benchmark-dir data/benchmarks/large \
  --skip-exact \
  --skip-qaoa \
  --severity-weight 32
```

## Demo Flow

1. Show the problem:
   "We need to decide which ambulances go to which incidents during a disaster."

2. Show the binary decision variable:
   "`x[A1,I4] = 1` means ambulance A1 is assigned to incident I4."

3. Explain QUBO:
   "The score rewards short distance and high severity, while penalties make
   invalid assignments expensive."

4. Run the small benchmark:
   - exact validates the optimum;
   - QAOA shows the quantum path works;
   - mention QAOA is slower locally and not quantum advantage.

5. Run medium safe mode:
   - exact and local QAOA are `N/A`;
   - greedy is feasible;
   - optimal flow is a stronger classical baseline.

6. Run medium or large with hard critical priority:
   - show critical coverage becomes 100%;
   - explain this is a policy choice: critical-first vs shortest-distance.

7. Close with honest conclusion:
   "The quantum workflow is validated on small cases. For larger cases, we now
   have the benchmark infrastructure and policy controls needed to evaluate
   scalable quantum-inspired or decomposed approaches next."

## Speaker Notes

QUBO:
A QUBO is a mathematical form where every decision is binary, and the solver
tries to minimise one score. In our case, the score combines travel distance,
incident severity, and penalties for invalid assignments.

QAOA:
QAOA is a hybrid quantum-classical algorithm. The quantum circuit samples
candidate binary assignments, and a classical optimiser updates the circuit
parameters to search for lower QUBO energy.

Multi-start QAOA:
QAOA can depend heavily on the starting angles. Multi-start QAOA runs several
deterministic starts and keeps the best result.

Exact enumeration:
Exact enumeration checks every possible binary assignment. It is useful for
small cases but impossible at medium and large scale.

Optimal flow:
Optimal flow is a strong classical baseline for this one-to-one assignment
version of the problem. It helps us avoid comparing QAOA only against a weak
greedy baseline.

Hard critical priority:
Hard priority is a policy mode. It tells the model to cover as many critical
incidents as possible before optimising distance tradeoffs.
