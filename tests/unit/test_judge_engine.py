from typing import Any, Type, TypeVar

import pytest
from pydantic import BaseModel

from src.domain.entities import GoldenTestCase, Step, Trajectory
from src.domain.interfaces.llm_provider import LLMProvider
from src.use_cases.judges.correctness import AnswerCorrectnessJudge
from src.use_cases.judges.engine import LLMJudgeEngine, LLMJudgeOutputSchema
from src.use_cases.judges.faithfulness import FaithfulnessJudge
from src.use_cases.judges.groundedness import GroundednessJudge
from src.use_cases.judges.hallucination import HallucinationJudge
from src.use_cases.judges.registry import JudgeRegistry
from src.use_cases.judges.templates import JudgePromptTemplate

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(LLMProvider):
    """Mock LLM Provider for unit testing judges deterministically."""

    def __init__(self) -> None:
        self.generate_text_calls: list[tuple[str, str | None]] = []
        self.generate_structured_calls: list[tuple[str, str | None]] = []
        self.text_responses: list[str] = []
        self.structured_responses: list[Any] = []
        self.raise_on_structured = False
        self.raise_on_text_count = 0

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        self.generate_text_calls.append((prompt, system_instruction))
        if self.raise_on_text_count > 0:
            self.raise_on_text_count -= 1
            raise RuntimeError("Mock text generation rate limit")
        if self.text_responses:
            return self.text_responses.pop(0)
        return '{"score": 1.0, "reasoning": "mock text success", "confidence": 0.95}'

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> T:
        self.generate_structured_calls.append((prompt, system_instruction))
        if self.raise_on_structured:
            raise RuntimeError("Mock structured generation error")
        if self.structured_responses:
            return self.structured_responses.pop(0)
        return response_schema(score=1.0, reasoning="mock structured success", confidence=0.9)


def test_judge_registry():
    """Tests LLM Judge registry registration, duplicates, and listing."""
    provider = MockLLMProvider()
    registry = JudgeRegistry()

    faith_judge = FaithfulnessJudge(provider)
    ground_judge = GroundednessJudge(provider)

    registry.register(faith_judge)
    registry.register(ground_judge)

    assert registry.get("Faithfulness") is faith_judge
    assert registry.get("Groundedness") is ground_judge
    assert "Faithfulness" in registry.list_judges()
    assert "Groundedness" in registry.list_judges()

    with pytest.raises(ValueError, match="already registered"):
        registry.register(faith_judge)

    with pytest.raises(ValueError, match="not registered"):
        registry.get("Unknown")


def test_judge_prompt_template_rendering():
    """Tests rendering of user and system prompts in JudgePromptTemplate."""
    template = JudgePromptTemplate(
        system_prompt="Role: {role}.",
        evaluation_instructions="Evaluate {input_val}.",
        scoring_rubric="Score 1.0 if good, else 0.0.",
    )

    sys = template.render_system(role="Auditor")
    assert sys == "Role: Auditor."

    user = template.render_user(input_val="assistant text")
    assert "Evaluate assistant text." in user
    assert "Score 1.0 if good, else 0.0." in user


@pytest.mark.anyio
async def test_judge_engine_structured_path():
    """Tests judge engine successful structured output generation path."""
    provider = MockLLMProvider()
    engine = LLMJudgeEngine(provider)

    template = JudgePromptTemplate(
        system_prompt="System instructions.",
        evaluation_instructions="Evaluate.",
        scoring_rubric="Rubric.",
    )

    res = await engine.execute(template, {})
    assert res.score == 1.0
    assert res.reasoning == "mock structured success"
    assert res.confidence == 0.9
    assert res.metadata["generation_mode"] == "structured"


@pytest.mark.anyio
async def test_judge_engine_fallback_path():
    """Tests judge engine fallback to text generation and manual parsing."""
    provider = MockLLMProvider()
    provider.raise_on_structured = True
    provider.text_responses = ['{"score": 0.8, "reasoning": "fallback parsed", "confidence": 0.85}']
    engine = LLMJudgeEngine(provider)

    template = JudgePromptTemplate(
        system_prompt="System instructions.",
        evaluation_instructions="Evaluate.",
        scoring_rubric="Rubric.",
    )

    res = await engine.execute(template, {})
    assert res.score == 0.8
    assert res.reasoning == "fallback parsed"
    assert res.confidence == 0.85
    assert res.metadata["generation_mode"] == "fallback_parsed"


@pytest.mark.anyio
async def test_judge_engine_fallback_json_markdown():
    """Tests fallback path with markdown JSON code blocks."""
    provider = MockLLMProvider()
    provider.raise_on_structured = True
    provider.text_responses = [
        "Some prefix text\n```json\n"
        '{"score": 0.5, "reasoning": "markdown json", "confidence": 0.7}\n'
        "```\nSuffix text"
    ]
    engine = LLMJudgeEngine(provider)

    template = JudgePromptTemplate(
        system_prompt="System instructions.",
        evaluation_instructions="Evaluate.",
        scoring_rubric="Rubric.",
    )

    res = await engine.execute(template, {})
    assert res.score == 0.5
    assert res.reasoning == "markdown json"
    assert res.confidence == 0.7


@pytest.mark.anyio
async def test_judge_engine_retries_and_exhaustion():
    """Tests retry backoff loop and final failure handling."""
    provider = MockLLMProvider()
    provider.raise_on_structured = True
    # Fail text generation 2 times, then succeed
    provider.raise_on_text_count = 2
    provider.text_responses = ['{"score": 1.0, "reasoning": "recovered", "confidence": 1.0}']

    engine = LLMJudgeEngine(provider, max_retries=3, initial_delay=0.01)
    template = JudgePromptTemplate(
        system_prompt="System instructions.",
        evaluation_instructions="Evaluate.",
        scoring_rubric="Rubric.",
    )

    res = await engine.execute(template, {})
    assert res.score == 1.0
    assert res.reasoning == "recovered"
    assert res.confidence == 1.0

    # Exhaust all retries completely
    provider_fail = MockLLMProvider()
    provider_fail.raise_on_structured = True
    provider_fail.raise_on_text_count = 5  # more than max_retries

    engine_fail = LLMJudgeEngine(provider_fail, max_retries=2, initial_delay=0.01)
    res_fail = await engine_fail.execute(template, {})
    assert res_fail.score == 0.0
    assert "failed after 3 attempts" in res_fail.reasoning
    assert res_fail.confidence == 0.0


@pytest.mark.anyio
async def test_faithfulness_judge_execution():
    """Tests FaithfulnessJudge end-to-end evaluation execution."""
    provider = MockLLMProvider()
    provider.structured_responses = [
        LLMJudgeOutputSchema(
            score=1.0, reasoning="Completely aligned with contexts", confidence=0.98
        )
    ]
    judge = FaithfulnessJudge(provider)

    case = GoldenTestCase(
        case_id="tc-f1",
        input_query="Flight JFK to LAX?",
        expected_output="UA100",
    )
    trajectory = Trajectory()
    trajectory.add_step(
        Step(
            step_number=1,
            response="Flight UA100 leaves at 10 AM.",
            metadata={"retrieved_contexts": ["UA100 flies from JFK to LAX daily at 10 AM."]},
        )
    )

    result = await judge.evaluate(case, trajectory)
    assert result.metric_name == "Faithfulness"
    assert result.score == 1.0
    assert result.reasoning == "Completely aligned with contexts"
    assert result.metadata["confidence"] == 0.98


@pytest.mark.anyio
async def test_groundedness_judge_execution():
    """Tests GroundednessJudge end-to-end evaluation execution."""
    provider = MockLLMProvider()
    provider.structured_responses = [
        LLMJudgeOutputSchema(score=0.0, reasoning="Violates maximum price limit", confidence=0.9)
    ]
    judge = GroundednessJudge(provider)

    case = GoldenTestCase(
        case_id="tc-g1",
        input_query="Flight under $300?",
        constraints={"max_price": 300},
    )
    trajectory = Trajectory()
    trajectory.add_step(Step(step_number=1, response="Booked flight UA100 for $450."))

    result = await judge.evaluate(case, trajectory)
    assert result.metric_name == "Groundedness"
    assert result.score == 0.0
    assert "Violates maximum price limit" in result.reasoning


@pytest.mark.anyio
async def test_correctness_judge_execution():
    """Tests AnswerCorrectnessJudge end-to-end evaluation execution."""
    provider = MockLLMProvider()
    provider.structured_responses = [
        LLMJudgeOutputSchema(score=1.0, reasoning="Matches expected output", confidence=0.9)
    ]
    judge = AnswerCorrectnessJudge(provider)

    case = GoldenTestCase(
        case_id="tc-c1",
        input_query="JFK to LAX?",
        expected_output="Flight UA100",
    )
    trajectory = Trajectory()
    trajectory.add_step(Step(step_number=1, response="Flight UA100"))

    result = await judge.evaluate(case, trajectory)
    assert result.metric_name == "AnswerCorrectness"
    assert result.score == 1.0


@pytest.mark.anyio
async def test_hallucination_judge_execution():
    """Tests HallucinationJudge end-to-end evaluation execution."""
    provider = MockLLMProvider()
    provider.structured_responses = [
        LLMJudgeOutputSchema(score=0.0, reasoning="No hallucinations detected", confidence=0.95)
    ]
    judge = HallucinationJudge(provider)

    case = GoldenTestCase(
        case_id="tc-h1",
        input_query="JFK to LAX?",
    )
    trajectory = Trajectory()
    trajectory.add_step(
        Step(
            step_number=1,
            response="Flight UA100",
            metadata={"contexts": ["Flight UA100 operates daily between JFK and LAX."]},
        )
    )

    result = await judge.evaluate(case, trajectory)
    assert result.metric_name == "Hallucination"
    assert result.score == 0.0


@pytest.mark.anyio
async def test_judge_missing_response_failure():
    """Tests judge error handling when SUT response is missing."""
    provider = MockLLMProvider()
    judge = FaithfulnessJudge(provider)

    case = GoldenTestCase(case_id="tc-fail", input_query="Query?")
    trajectory = Trajectory()  # Empty trajectory, no steps/response

    result = await judge.evaluate(case, trajectory)
    assert result.score == 0.0
    assert "Failed to prepare variables" in result.reasoning
