import json
from pathlib import Path


REQUIRED_FIELDS = {
    "timestamp": str,
    "cpu": (int, float),
    "mem": (int, float),
    "disk": (int, float),
    "server": str,
    "severity": str,
    "duration_seconds": (int, float),
}


def validate_anomaly_event(event):
    """Validate the structure of an ICLIM anomaly event."""

    if not isinstance(event, dict):
        raise ValueError("Anomaly event must be a dictionary.")

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in event:
            raise ValueError(f"Missing required field: {field}")

        if not isinstance(event[field], expected_type):
            raise ValueError(
                f"Invalid type for '{field}': "
                f"expected {expected_type}, got {type(event[field])}"
            )


def normalize_severity(severity):
    """Normalize ICLIM anomaly severity for the AI context."""

    normalized = severity.strip().lower()

    valid_severities = {
        "unusual": "UNUSUAL",
        "warning": "WARNING",
        "critical": "CRITICAL",
    }

    if normalized not in valid_severities:
        raise ValueError(f"Unknown anomaly severity: {severity}")

    return valid_severities[normalized]


def build_incident_context(event):
    """Build Incident Context V1 from an ICLIM anomaly event."""

    validate_anomaly_event(event)

    return {
        "incident": {
            "timestamp": event["timestamp"],
            "server": event["server"],
            "severity": normalize_severity(event["severity"]),
            "anomaly_duration_seconds": event["duration_seconds"],
        },
        "resources": {
            "cpu_percent": event["cpu"],
            "memory_percent": event["mem"],
            "disk_percent": event["disk"],
        },
    }


def load_anomaly_event(filename):
    """Load the most recent anomaly event from a JSONL file."""

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(f"Anomaly file not found: {filename}")

    with path.open("r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        raise ValueError("Anomaly event file is empty.")

    return json.loads(lines[-1])


if __name__ == "__main__":
    event = load_anomaly_event("logs/anomaly_events.jsonl")
    context = build_incident_context(event)

    print(json.dumps(context, indent=2))