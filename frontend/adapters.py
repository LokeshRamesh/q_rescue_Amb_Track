"""Adapters between the Streamlit demo and the Q-Rescue domain model.

The frontend still uses UI-friendly data for forms, charts and maps. The
backend domain model in ``src/q_rescue/domain/models.py`` uses stricter
canonical values:

- Severity: 1 LOW, 2 MEDIUM, 3 HIGH, 4 CRITICAL
- DisasterCategory: generic, flood, industrial_accident, city_wide_emergency
- Location(x, y)
- Ambulance(id, location, status)

This module keeps that mapping explicit until the frontend calls the backend
service layer directly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum, IntEnum


class Severity(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class DisasterCategory(Enum):
    GENERIC = "generic"
    FLOOD = "flood"
    INDUSTRIAL_ACCIDENT = "industrial_accident"
    CITY_WIDE_EMERGENCY = "city_wide_emergency"


@dataclass(frozen=True)
class Location:
    x: float
    y: float


@dataclass(frozen=True)
class Ambulance:
    id: str
    location: Location
    status: str = "Available"


DISASTER_CATEGORY_OPTIONS = {
    "Generic incident": DisasterCategory.GENERIC,
    "Flood": DisasterCategory.FLOOD,
    "Industrial accident": DisasterCategory.INDUSTRIAL_ACCIDENT,
    "City-wide emergency": DisasterCategory.CITY_WIDE_EMERGENCY,
}


SEVERITY_OPTIONS = {
    "Low": Severity.LOW,
    "Medium": Severity.MEDIUM,
    "High": Severity.HIGH,
    "Critical": Severity.CRITICAL,
}


SHEFFIELD_LOCATIONS = {
    "Sheffield City Centre": Location(53.3811, -1.4701),
    "Northern General Hospital": Location(53.4109, -1.4587),
    "Royal Hallamshire Hospital": Location(53.3785, -1.4939),
    "Meadowhall": Location(53.4148, -1.4103),
    "Hillsborough": Location(53.4021, -1.5002),
    "Darnall": Location(53.3845, -1.4135),
    "Ecclesall Road": Location(53.3704, -1.4978),
    "Attercliffe": Location(53.3950, -1.4330),
}


def category_from_label(label: str) -> DisasterCategory:
    return DISASTER_CATEGORY_OPTIONS.get(label, DisasterCategory.GENERIC)


def location_from_label(label: str) -> Location:
    return SHEFFIELD_LOCATIONS.get(label, SHEFFIELD_LOCATIONS["Sheffield City Centre"])


def ambulance_from_route(route: dict) -> Ambulance:
    """Convert a frontend ambulance route row into the backend shape."""
    return Ambulance(
        id=str(route["Ambulance ID"]),
        location=Location(
            x=float(route["Start Latitude"]),
            y=float(route["Start Longitude"]),
        ),
        status="Available",
    )


def to_domain_payload(simulation: dict) -> dict:
    """Return a JSON-friendly payload aligned with backend domain objects."""
    severity = Severity(int(simulation["severity"]))
    category = category_from_label(str(simulation["disaster_type"]))
    location = location_from_label(str(simulation["location"]))

    return {
        "incident": {
            "id": simulation.get("incident_id", "frontend-demo-incident"),
            "location": asdict(location),
            "severity": severity.name,
            "severity_value": int(severity),
            "category": category.value,
        },
        "ui_context": {
            "affected_population": simulation.get("affected_population", 0),
            "available_ambulances": simulation.get("available_ambulances", 0),
            "available_rescue_teams": simulation.get("available_rescue_teams", 0),
            "available_food_units": simulation.get("available_food_units", 0),
        },
    }
