from typing import Any

from src.domain.entities import GoldenTestCase, Trajectory
from src.use_cases.judges.base import BaseLLMJudge
from src.use_cases.judges.templates import CORRECTNESS_TEMPLATE, JudgePromptTemplate


class AnswerCorrectnessJudge(BaseLLMJudge):
    """LLM Judge evaluating if assistant response matches the reference ground truth response."""

    @property
    def name(self) -> str:
        return "AnswerCorrectness"

    @property
    def prompt_template(self) -> JudgePromptTemplate:
        return CORRECTNESS_TEMPLATE

    def prepare_variables(
        self, test_case: GoldenTestCase, trajectory: Trajectory
    ) -> dict[str, Any]:
        response = trajectory.final_response
        if not response:
            raise ValueError("Trajectory does not contain a final response.")
        if not test_case.expected_output:
            raise ValueError("GoldenTestCase does not contain expected_output.")

        return {
            "query": test_case.input_query,
            "expected_output": test_case.expected_output,
            "response": response,
        }
