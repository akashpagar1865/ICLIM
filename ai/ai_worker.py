import json

from ai.context_builder import (
    load_anomaly_event,
    build_incident_context,
)
from ai.incident_explainer import IncidentExplainer
from ai.operational_assistant import OperationalAssistant
from ai.result_store import save_ai_incident


ANOMALY_FILE = "logs/anomaly_events.jsonl"
AI_RESULT_FILE = "logs/ai_incidents.jsonl"


def load_latest_ai_timestamp():
    try:
        with open(AI_RESULT_FILE, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]

        if not lines:
            return None

        return json.loads(lines[-1])["timestamp"]

    except FileNotFoundError:
        return None


def main():
    event = load_anomaly_event(ANOMALY_FILE)

    if not event:
        print("No anomaly event available.")
        return

    context = build_incident_context(event)

    incident_timestamp = context["incident"]["timestamp"]
    latest_ai_timestamp = load_latest_ai_timestamp()

    if latest_ai_timestamp == incident_timestamp:
        print(f"AI result already exists for {incident_timestamp}.")
        return

    print(f"Generating AI result for {incident_timestamp}...")

    explanation = IncidentExplainer().explain(context)
    recommendations = OperationalAssistant().recommend(context)

    record = save_ai_incident(
        context,
        explanation,
        recommendations,
    )

    print(json.dumps(record, indent=2))
    print("AI incident result saved successfully.")


if __name__ == "__main__":
    main()