import json

from ai.providers.groq_provider import GroqProvider


class OperationalAssistant:
    """AI assistant that recommends evidence-based investigation steps."""

    def __init__(self, provider=None):
        self.provider = provider or GroqProvider()

    def recommend(self, context):
        prompt = f"""
Analyze the following ICLIM incident context.

Your job is to answer:

"What should an engineer investigate next?"

Rules:
- Use ONLY the evidence provided in the ICLIM incident context.
- Do not invent a root cause, process, service, deployment, or other fact.
- Do not claim causation unless the evidence explicitly supports it.
- Preserve the ICLIM severity exactly as provided.
- ICLIM severity values are UNUSUAL, WARNING, and CRITICAL.
- Do not confuse the Python logging level WARNING with ICLIM severity.
- Do not recalculate or change the ICLIM severity.
- anomaly_duration_seconds represents the persistence duration reported
  by ICLIM. Do not construct exact anomaly start/end timestamps unless
  explicitly provided.
- Recommend investigation steps, not remediation.
- Do not recommend restarting, killing, modifying, or changing anything
  automatically.
- Recommendations should be practical for a Linux/DevOps/SRE engineer.
- Base recommendations on the evidence available.
- If evidence is insufficient, explicitly say what is unknown.
- Keep the human engineer responsible for investigation and action.
- Return ONLY valid JSON.
- Do not wrap the JSON in markdown code fences.

Return exactly this structure:

{{
  "incident": "...",
  "severity": "...",
  "investigation_priority": "HIGH|MEDIUM|LOW",
  "recommended_checks": [
    "...",
    "...",
    "..."
  ],
  "evidence_basis": [
    "...",
    "..."
  ],
  "unknowns": [
    "...",
    "..."
  ],
  "human_action_required": "..."
}}

ICLIM incident context:
{json.dumps(context, indent=2)}
"""
        response_schema = {
    "type": "json_schema",
    "json_schema": {
        "name": "iclim_operational_assistant",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "incident": {
                    "type": "string"
                },
                "severity": {
                    "type": "string",
                    "enum": ["UNUSUAL", "WARNING", "CRITICAL"]
                },
                "investigation_priority": {
                    "type": "string",
                    "enum": ["HIGH", "MEDIUM", "LOW"]
                },
                "recommended_checks": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "evidence_basis": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "unknowns": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "human_action_required": {
                    "type": "string"
                }
            },
            "required": [
                "incident",
                "severity",
                "investigation_priority",
                "recommended_checks",
                "evidence_basis",
                "unknowns",
                "human_action_required"
            ],
            "additionalProperties": False
        }
    }
}
        response = self.provider.generate(
            prompt,
            response_format=response_schema,
        )

        try:
            result = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "AI provider returned invalid JSON."
            ) from exc

        required_fields = {
            "incident",
            "severity",
            "investigation_priority",
            "recommended_checks",
            "evidence_basis",
            "unknowns",
            "human_action_required",
        }

        missing_fields = required_fields - result.keys()

        if missing_fields:
            raise RuntimeError(
                "AI response is missing required fields: "
                + ", ".join(sorted(missing_fields))
            )

        return result