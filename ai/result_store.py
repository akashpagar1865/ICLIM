import json
from pathlib import Path


DEFAULT_OUTPUT = Path("logs/ai_incidents.jsonl")


def save_ai_incident(
    context,
    incident_explanation,
    operational_assistant,
    output_file=DEFAULT_OUTPUT,
):
    """Persist combined AI results for one ICLIM incident."""

    incident = context["incident"]

    record = {
        "timestamp": incident["timestamp"],
        "server": incident["server"],
        "severity": incident["severity"],
        "incident_explanation": incident_explanation,
        "operational_assistant": operational_assistant,
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record