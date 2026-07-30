from abc import abstractmethod
from typing import Any

from src.domain.entities import GoldenTestCase, MetricResult, Trajectory
from src.domain.interfaces.evaluator import BaseEvaluator
from src.domain.interfaces.llm_provider import LLMProvider
from src.use_cases.judges.engine import LLMJudgeEngine
from src.use_cases.judges.templates import JudgePromptTemplate


class BaseLLMJudge(BaseEvaluator):
    """Common base abstraction for all LLM-based judges."""

    def __init__(self, provider: LLMProvider, engine: LLMJudgeEngine | None = None) -> None:
        self.provider = provider
        self.engine = engine or LLMJudgeEngine(provider)

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the judge evaluator."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> JudgePromptTemplate:
        """The prompt template defining this judge."""
        pass

    @abstractmethod
    def prepare_variables(
        self, test_case: GoldenTestCase, trajectory: Trajectory
    ) -> dict[str, Any]:
        """Prepares the variables to be interpolated into the prompt templates."""
        pass

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        """Executes the judge logic via the LLMJudgeEngine and returns a MetricResult."""
        try:
            variables = self.prepare_variables(test_case, trajectory)
        except Exception as e:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                reasoning=f"Failed to prepare variables for LLM Judge: {str(e)}",
                metadata={"error": str(e), "exception_type": type(e).__name__},
            )

        judge_result = await self.engine.execute(self.prompt_template, variables)

        # Convert score to float in case LLM returned boolean or other format
        try:
            score_val = float(judge_result.score)
        except (ValueError, TypeError):
            score_val = 1.0 if judge_result.score else 0.0

        return MetricResult(
            metric_name=self.name,
            score=score_val,
            reasoning=judge_result.reasoning,
            metadata={
                "confidence": judge_result.confidence,
                "raw_output": judge_result.raw_output,
                **judge_result.metadata,
            },
        )
