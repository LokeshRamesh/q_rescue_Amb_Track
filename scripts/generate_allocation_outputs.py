from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from q_rescue.services.allocation_output import (
    AllocationSettings,
    build_allocation_output_from_benchmark,
    build_allocation_output_from_request,
    write_json_output,
)


def main() -> None:
    args = _parse_args()

    if args.request_json:
        request = _read_json(args.request_json)
        allocation_result = build_allocation_output_from_request(request)
        output_path = args.output or Path("data/outputs/allocation_results.json")
        write_json_output(allocation_result, output_path)
        print(f"Wrote {output_path}")
        return

    settings = AllocationSettings(
        critical_priority=args.critical_priority,
        run_qaoa=args.run_qaoa,
        run_exact=args.run_exact,
        exact_variable_limit=args.exact_variable_limit,
        qaoa_variable_limit=args.qaoa_variable_limit,
        qaoa_attempts=args.qaoa_attempts,
        seed=args.seed,
    )
    generated = []
    for benchmark_dir in sorted(args.benchmark_root.iterdir()):
        if not benchmark_dir.is_dir() or not (benchmark_dir / "scenario.json").exists():
            continue
        allocation_result = build_allocation_output_from_benchmark(benchmark_dir, settings=settings)
        output_path = benchmark_dir / "allocation_results.json"
        write_json_output(allocation_result, output_path)
        generated.append(output_path)

    for output_path in generated:
        print(f"Wrote {output_path}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate UI-ready allocation JSON from a UI request or benchmark exports"
    )
    parser.add_argument(
        "--request-json",
        type=Path,
        help="UI request JSON describing the incident/disaster to simulate",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path when --request-json is provided",
    )
    parser.add_argument(
        "--benchmark-root",
        type=Path,
        default=Path("data/benchmarks"),
        help="Directory containing benchmark scenario folders",
    )
    parser.add_argument(
        "--critical-priority",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Prioritise covering critical incidents before lower severity incidents",
    )
    parser.add_argument(
        "--run-exact",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run exact enumeration when within the variable limit",
    )
    parser.add_argument(
        "--run-qaoa",
        action="store_true",
        help="Run local QAOA simulation when within the variable limit",
    )
    parser.add_argument("--exact-variable-limit", type=int, default=24)
    parser.add_argument("--qaoa-variable-limit", type=int, default=24)
    parser.add_argument("--qaoa-attempts", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object at top level of {path}")
    return data


if __name__ == "__main__":
    main()
