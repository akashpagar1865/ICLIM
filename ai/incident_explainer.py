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
- Do not invent a root cause.
- Do not claim causation unless the evidence explicitly supports it.
- Clearly distinguish observed evidence from interpretation.
- Identify what remains unknown.
- Provide practical investigation guidance.
- Do not recalculate or change the ICLIM severity.
- Return ONLY valid JSON.
- Do not wrap the JSON in markdown code fences.

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