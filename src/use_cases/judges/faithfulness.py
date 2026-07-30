from typing import Any

from src.domain.entities import GoldenTestCase, Trajectory
from src.use_cases.judges.base import BaseLLMJudge
from src.use_cases.judges.templates import FAITHFULNESS_TEMPLATE, JudgePromptTemplate
from src.use_cases.metrics.evaluators import extract_retrieved_contexts


class FaithfulnessJudge(BaseLLMJudge):
    """LLM Judge evaluating if assistant response is supported only by retrieved contexts."""

    @property
    def name(self) -> str:
        return "Faithfulness"

    @property
    def prompt_template(self) -> JudgePromptTemplate:
        return FAITHFULNESS_TEMPLATE

    def prepare_variables(
        self, test_case: GoldenTestCase, trajectory: Trajectory
    ) -> dict[str, Any]:
        response = trajectory.final_response
        if not response:
            raise ValueError("Trajectory does not contain a final response.")

        contexts = extract_retrieved_contexts(trajectory)
        context_str = "\n".join(f"- {c}" for c in contexts) if contexts else "No context retrieved."
        return {
            "context": context_str,
            "response": response,
        }
