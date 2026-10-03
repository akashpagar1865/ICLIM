import json

from ai.providers.groq_provider import GroqProvider


class IncidentExplainer:
    """Generate a structured explanation for an ICLIM incident."""

    def __init__(self, provider=None):
        self.provider = provider or GroqProvider()

    def explain(self, context):
        """Generate and parse an incident explanation."""

        prompt = f"""
Analyze the following ICLIM incident context.

Your job is to explain what happened using ONLY the evidence provided.

Rules:
- Use ONLY the evidence provided in the ICLIM incident context.
- Do not invent a root cause, process, service, deployment, or other fact.
- Do not claim causation unless the provided evidence explicitly supports it.
- Clearly distinguish observed evidence from interpretation.
- Preserve the ICLIM severity exactly as provided.
- IMPORTANT: ICLIM severity values are UNUSUAL, WARNING, and CRITICAL.
- A log line may contain the Python logging level WARNING. Do not confuse
  that logging level with the ICLIM incident severity.
- The Prometheus evidence represents a 5-minute observation window.
- Prometheus values in this context are sampled at 60-second intervals.
- Do not claim that Prometheus "missed" an event unless the evidence
  establishes that conclusion. Instead, describe the discrepancy between
  the ICLIM event and Prometheus observations.
- Do not describe a resource as "normal" unless the provided evidence
  establishes a baseline. You may describe a resource as stable,
  increasing, decreasing, or relatively unchanged when supported by the
  supplied values.
- Do not recalculate or change the ICLIM severity.
- Identify what remains unknown.
- Provide practical investigation guidance based on the available evidence.
- Return ONLY valid JSON.
- Do not wrap the JSON in markdown code fences.
- Treat differences between ICLIM event values and Prometheus values as
  discrepancies unless the context explicitly establishes why they differ.
- NEVER state that Prometheus missed, failed to capture, or sampled around
  an event unless the evidence explicitly proves the timing relationship.
- Do not propose a specific explanation for a metric discrepancy as if it
  were established fact. If relevant, identify possible explanations as
  unknowns or investigation items.
- Do not describe values as moderate, high, low, normal, abnormal, or
  significant unless the supplied evidence explicitly establishes that
  characterization.
- anomaly_duration_seconds represents the persistence duration reported
  by ICLIM. Do not construct an exact anomaly start or end timestamp from
  it unless those timestamps are explicitly provided.

Return exactly this structure:

{{
  "incident": "...",
  "severity": "...",
  "observed_evidence": [
    "...",
    "..."
  ],
  "timeline": [
    "...",
    "..."
  ],
  "explanation": "...",
  "evidence_strength": {{
    "level": "HIGH|MEDIUM|LOW",
    "reason": "..."
  }},
  "unknowns": [
    "...",
    "..."
  ],
  "investigation_guidance": [
    "...",
    "..."
  ]
}}

ICLIM incident context:

{json.dumps(context, indent=2)}
"""

        response = self.provider.generate(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "AI provider returned invalid JSON."
            ) from exc