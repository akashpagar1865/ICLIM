
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


def start_metrics_server():
    start_http_server(8000)
