import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


REQUIRED_FIELDS = {
    "timestamp": str,
    "cpu": (int, float),
    "mem": (int, float),
    "disk": (int, float),
    "server": str,
    "severity": str,
    "duration_seconds": (int, float),
}

PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://localhost:9090"
)

EVIDENCE_WINDOW_MINUTES = 5


def validate_anomaly_event(event):
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
    normalized = severity.strip().lower()

    valid_severities = {
        "unusual": "UNUSUAL",
        "warning": "WARNING",
        "critical": "CRITICAL",
    }

    if normalized not in valid_severities:
        raise ValueError(f"Unknown anomaly severity: {severity}")

    return valid_severities[normalized]


def parse_timestamp(timestamp):
    return datetime.strptime(
        timestamp,
        "%Y-%m-%d %H:%M:%S"
    )


def query_prometheus_range(query, start_time, end_time):
    params = urlencode({
        "query": query,
        "start": start_time.timestamp(),
        "end": end_time.timestamp(),
        "step": "60",
    })

    url = f"{PROMETHEUS_URL}/api/v1/query_range?{params}"

    with urlopen(url, timeout=5) as response:
        data = json.load(response)

    if data.get("status") != "success":
        raise RuntimeError("Prometheus query failed.")

    return data["data"]["result"]


def collect_prometheus_evidence(timestamp):
    incident_time = parse_timestamp(timestamp)

    start_time = incident_time - timedelta(
        minutes=EVIDENCE_WINDOW_MINUTES
    )

    queries = {
        "cpu_percent": (
            '100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'
        ),
        "memory_percent": (
            '(1 - (node_memory_MemAvailable_bytes / '
            'node_memory_MemTotal_bytes)) * 100'
        ),
        "disk_percent": (
            '100 * (1 - (node_filesystem_avail_bytes{mountpoint="/"} / '
            'node_filesystem_size_bytes{mountpoint="/"}))'
        ),
    }

    evidence = {}

    for name, query in queries.items():
        try:
            evidence[name] = query_prometheus_range(
                query,
                start_time,
                incident_time,
            )
        except Exception as exc:
            evidence[name] = {
                "error": str(exc)
            }

    return {
        "window": {
            "start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": incident_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": EVIDENCE_WINDOW_MINUTES,
        },
        "metrics": evidence,
    }

def collect_log_evidence(timestamp):
    """Collect ICLIM log entries from the 5-minute window before an incident."""

    log_path = Path("logs/iclim.log")
    incident_time = parse_timestamp(timestamp)

    start_time = incident_time - timedelta(
        minutes=EVIDENCE_WINDOW_MINUTES
    )

    if not log_path.exists():
        return {
            "error": f"Log file not found: {log_path}"
        }

    matching_logs = []

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                log_timestamp = datetime.strptime(
                    line[:19],
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                continue

            if start_time <= log_timestamp <= incident_time:
                matching_logs.append(line)

    return {
        "window": {
            "start": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": incident_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_minutes": EVIDENCE_WINDOW_MINUTES,
        },
        "entries": matching_logs,
        "count": len(matching_logs),
    }


def build_incident_context(event):
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
        "prometheus_evidence": collect_prometheus_evidence(
            event["timestamp"]
        ),
        "log_evidence": collect_log_evidence(
            event["timestamp"]
        ),
    }


def load_anomaly_event(filename):
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Anomaly file not found: {filename}"
        )

    with path.open("r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]

    if not lines:
        raise ValueError("Anomaly event file is empty.")

    return json.loads(lines[-1])


if __name__ == "__main__":
    event = load_anomaly_event("logs/anomaly_events.jsonl")
    context = build_incident_context(event)

    print(json.dumps(context, indent=2))