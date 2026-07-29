from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Abstract interface for pluggable LLM integrations."""

    @abstractmethod
    async def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generates a simple text response given a prompt and optional system instructions."""
        pass

    @abstractmethod
    async def generate_structured(
        self, prompt: str, response_schema: type[T], system_instruction: str | None = None
    ) -> T:
        """Generates a structured response parsing the model's output
        into the target Pydantic schema.

        This is critical for LLM-as-a-judge evaluators that must output
        structured evaluation scores.
        """
        pass
