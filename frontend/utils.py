from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


CACHE_DIR = Path(__file__).resolve().parents[1] / "cache"
LATEST_SIMULATION_FILE = CACHE_DIR / "latest_frontend_simulation.json"


def save_simulation_results(results: dict) -> Path:
    """Save the latest frontend demo simulation to a lightweight JSON cache.

    This is temporary demo persistence. Once the backend service layer is
    connected, this should be replaced by API/database persistence.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "results": results,
    }
    LATEST_SIMULATION_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return LATEST_SIMULATION_FILE


def load_latest_simulation_results() -> dict | None:
    """Restore the most recent cached demo simulation, if available."""
    if not LATEST_SIMULATION_FILE.exists():
        return None

    try:
        payload = json.loads(LATEST_SIMULATION_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    results = payload.get("results")
    if not isinstance(results, dict):
        return None

    results["restored_from_cache"] = True
    results["cache_saved_at"] = payload.get("saved_at")
    return results


def calculate_disaster_metrics(
    severity,
    affected_population,
    available_ambulances,
    available_rescue_teams,
    available_food_units
):
    """
    This function generates simulated disaster response metrics.
    Severity follows the backend domain model: 1=LOW, 2=MEDIUM, 3=HIGH,
    4=CRITICAL.
    """

    severity = max(1, min(4, int(severity)))
    severity_ratio = severity / 4

    estimated_casualties = int(severity_ratio * 0.12 * affected_population)

    response_time = max(5, int(34 - (available_ambulances * 0.4) - (available_rescue_teams * 0.3) + severity * 3))

    resources_needed = int((affected_population / 1000) + (severity * 12))

    optimisation_score = min(100, int(55 + severity * 8 + available_rescue_teams * 0.8))

    recommended_ambulances = max(available_ambulances, int(severity * 5))
    recommended_rescue_teams = max(available_rescue_teams, int(severity * 3))
    recommended_food_units = max(available_food_units, int(affected_population / 300))

    critical_risk = min(55, severity * 12)
    high_risk = min(35, severity * 8)
    medium_risk = max(10, 30 - severity * 3)
    low_risk = max(0, 100 - critical_risk - high_risk - medium_risk)

    return {
        "estimated_casualties": estimated_casualties,
        "response_time": response_time,
        "resources_needed": resources_needed,
        "optimisation_score": optimisation_score,
        "recommended_ambulances": recommended_ambulances,
        "recommended_rescue_teams": recommended_rescue_teams,
        "recommended_food_units": recommended_food_units,
        "critical_risk": critical_risk,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
        "low_risk": low_risk
    }
