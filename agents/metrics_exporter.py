import json
from pathlib import Path
from prometheus_client import Gauge, Counter, start_http_server

agent_status = Gauge(
    "iclim_agent_status",
    "Whether the ICLIM agent is running"
)

def set_agent_status(value):
    agent_status.set(value)

model_loaded = Gauge(
    "iclim_model_loaded",
    "Whether the ICLIM anomaly detection model is loaded"
)

bootstrap_completed = Gauge(
    "iclim_bootstrap_completed",
    "Whether ICLIM bootstrap completed successfully"
)

anomaly_total = Counter(
    "iclim_anomaly_total",
    "Total number of ICLIM anomalies by severity",
    ["severity"]
)

monitoring_cycles = Counter(
    "iclim_monitoring_cycles_total",
    "Total number of monitoring cycles completed by ICLIM"
)


ai_result_available = Gauge(
    "iclim_ai_result_available",
    "Whether an AI result is available for the latest incident"
)

ai_incident_severity = Gauge(
    "iclim_ai_incident_severity",
    "Latest ICLIM AI incident severity",
    ["severity"]
)

ai_investigation_priority = Gauge(
    "iclim_ai_investigation_priority",
    "Latest AI investigation priority",
    ["priority"]
)

def refresh_ai_metrics(filename="logs/ai_incidents.jsonl"):
    """Refresh AI Prometheus metrics from the latest persisted result."""

    try:
        path = Path(filename)

        if not path.exists():
            set_ai_result_available(0)
            ai_incident_severity.clear()
            ai_investigation_priority.clear()
            return

        with path.open("r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]

        if not lines:
            set_ai_result_available(0)
            ai_incident_severity.clear()
            ai_investigation_priority.clear()
            return

        record = json.loads(lines[-1])

        set_ai_result_available(1)

        set_ai_incident_severity(
            record["severity"]
        )

        set_ai_investigation_priority(
            record["operational_assistant"]["investigation_priority"]
        )

    except (OSError, json.JSONDecodeError, KeyError):
        set_ai_result_available(0)
        ai_incident_severity.clear()
        ai_investigation_priority.clear()


def set_ai_result_available(value):
    ai_result_available.set(value)


def set_ai_incident_severity(severity):
    ai_incident_severity.clear()
    ai_incident_severity.labels(severity=severity).set(1)


def set_ai_investigation_priority(priority):
    ai_investigation_priority.clear()
    ai_investigation_priority.labels(priority=priority).set(1)

def start_metrics_server():
    start_http_server(8000)
