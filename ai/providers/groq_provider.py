import os

from groq import Groq

from ai.providers.base import AIProvider


class GroqProvider(AIProvider):
    """Groq implementation of the ICLIM AI provider interface."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GROQ_API_KEY environment variable is not configured."
            )

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

        self.client = Groq(api_key=self.api_key)

    def generate(self, context):
        """Generate an AI response from incident context."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the AI incident interpretation layer "
                        "for ICLIM. Analyze only the operational evidence "
                        "provided in the context. Do not invent root causes "
                        "or facts that are not supported by the evidence."
                        "When requested, return the response as valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": str(context),
                },
            ],
            response_format={"type": "json_object"},
        )

        return response.choices[0].message.content