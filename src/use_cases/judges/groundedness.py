from typing import Any

from src.domain.entities import GoldenTestCase, Trajectory
from src.use_cases.judges.base import BaseLLMJudge
from src.use_cases.judges.templates import GROUNDEDNESS_TEMPLATE, JudgePromptTemplate


class GroundednessJudge(BaseLLMJudge):
    """LLM Judge evaluating if assistant response satisfies user query and constraints."""

    @property
    def name(self) -> str:
        return "Groundedness"

    @property
    def prompt_template(self) -> JudgePromptTemplate:
        return GROUNDEDNESS_TEMPLATE

    def prepare_variables(
        self, test_case: GoldenTestCase, trajectory: Trajectory
    ) -> dict[str, Any]:
        response = trajectory.final_response
        if not response:
            raise ValueError("Trajectory does not contain a final response.")

        constraints_str = (
            ", ".join(f"{k}: {v}" for k, v in test_case.constraints.items())
            if test_case.constraints
            else "None"
        )
        return {
            "query": test_case.input_query,
            "constraints": constraints_str,
            "response": response,
        }
