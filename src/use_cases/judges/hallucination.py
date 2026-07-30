from typing import Any

from src.domain.entities import GoldenTestCase, Trajectory
from src.use_cases.judges.base import BaseLLMJudge
from src.use_cases.judges.templates import HALLUCINATION_TEMPLATE, JudgePromptTemplate
from src.use_cases.metrics.evaluators import extract_retrieved_contexts


class HallucinationJudge(BaseLLMJudge):
    """LLM Judge specifically auditing assistant response for hallucinations.

    Checks claims relative to retrieved context.
    """

    @property
    def name(self) -> str:
        return "Hallucination"

    @property
    def prompt_template(self) -> JudgePromptTemplate:
        return HALLUCINATION_TEMPLATE

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
