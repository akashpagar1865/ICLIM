from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Interface for ICLIM AI providers."""

    @abstractmethod
    def generate(self, context):
        """Generate an AI response from incident context."""
        raise NotImplementedError