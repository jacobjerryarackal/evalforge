import logging
from typing import Dict, List

from src.use_cases.judges.base import BaseLLMJudge

logger = logging.getLogger("evaluation.judges.registry")


class JudgeRegistry:
    """Registry for discovery, registration, and duplicate validation of LLM Judges."""

    def __init__(self) -> None:
        self._judges: Dict[str, BaseLLMJudge] = {}

    def register(self, judge: BaseLLMJudge) -> None:
        """Registers a judge instance. Raises ValueError if name is already registered."""
        name = judge.name
        if name in self._judges:
            raise ValueError(f"Judge with name '{name}' is already registered.")
        self._judges[name] = judge
        logger.info(f"Registered LLM Judge: {name}")

    def get(self, name: str) -> BaseLLMJudge:
        """Retrieves a registered judge by name."""
        if name not in self._judges:
            raise ValueError(f"Judge '{name}' is not registered.")
        return self._judges[name]

    def list_judges(self) -> List[str]:
        """Lists the names of all registered judges."""
        return list(self._judges.keys())

    def get_all(self) -> List[BaseLLMJudge]:
        """Returns all registered judge instances."""
        return list(self._judges.values())
