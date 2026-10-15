import json
import os

from ai.context_builder import (
    load_anomaly_event,
    build_incident_context,
)
from ai.incident_explainer import IncidentExplainer
from ai.operational_assistant import OperationalAssistant
from ai.result_store import save_ai_incident


ANOMALY_FILE = "logs/anomaly_events.jsonl"
AI_RESULT_FILE = "logs/ai_incidents.jsonl"

# Only incidents at or above this severity are sent to the LLM.
# Brief UNUSUAL blips are common; explaining each one wastes the
# provider's daily token quota (Groq free tier: 200k tokens/day).
SEVERITY_RANK = {"unusual": 1, "warning": 2, "critical": 3}
AI_MIN_SEVERITY = os.getenv("AI_MIN_SEVERITY", "warning").lower()


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

    severity = str(event.get("severity", "")).lower()

    if SEVERITY_RANK.get(severity, 0) < SEVERITY_RANK.get(AI_MIN_SEVERITY, 2):
        print(
            f"Latest incident is {severity.upper()} "
            f"(below {AI_MIN_SEVERITY.upper()}); no AI analysis needed."
        )
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