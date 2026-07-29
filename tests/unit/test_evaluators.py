import pytest

from src.domain.entities import GoldenTestCase, Step, ToolCall, Trajectory
from src.domain.value_objects import Cost, Latency, TokenUsage
from src.use_cases.metrics.evaluators import (
    ContextPrecisionEvaluator,
    ContextRecallEvaluator,
    CostEvaluator,
    LatencyEvaluator,
    TokenUsageEvaluator,
    ToolCallingEvaluator,
)


@pytest.mark.anyio
async def test_latency_evaluator():
    evaluator = LatencyEvaluator(default_max_latency=5.0)

    # Under threshold
    t1 = Trajectory()
    t1.add_step(Step(step_number=1, thought="", latency=Latency(seconds=3.0)))
    case = GoldenTestCase(case_id="tc-1", input_query="", constraints={})
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0
    assert "under the threshold" in res1.reasoning

    # Over threshold
    t2 = Trajectory()
    t2.add_step(Step(step_number=1, thought="", latency=Latency(seconds=6.0)))
    res2 = await evaluator.evaluate(case, t2)
    assert res2.score == 0.0
    assert "exceeds the threshold" in res2.reasoning

    # Case constraint override
    case_override = GoldenTestCase(case_id="tc-2", input_query="", constraints={"max_latency": 8.0})
    res3 = await evaluator.evaluate(case_override, t2)
    assert res3.score == 1.0


@pytest.mark.anyio
async def test_token_usage_evaluator():
    evaluator = TokenUsageEvaluator(default_max_tokens=100)
    case = GoldenTestCase(case_id="tc-1", input_query="")

    t1 = Trajectory()
    t1.add_step(
        Step(
            step_number=1,
            thought="",
            token_usage=TokenUsage(prompt_tokens=40, completion_tokens=50, total_tokens=90),
        )
    )
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0

    t2 = Trajectory()
    t2.add_step(
        Step(
            step_number=1,
            thought="",
            token_usage=TokenUsage(prompt_tokens=80, completion_tokens=50, total_tokens=130),
        )
    )
    res2 = await evaluator.evaluate(case, t2)
    assert res2.score == 0.0


@pytest.mark.anyio
async def test_cost_evaluator():
    evaluator = CostEvaluator(default_max_cost=0.01)
    case = GoldenTestCase(case_id="tc-1", input_query="")

    t1 = Trajectory()
    t1.add_step(Step(step_number=1, thought="", cost=Cost(amount=0.005)))
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0

    t2 = Trajectory()
    t2.add_step(Step(step_number=1, thought="", cost=Cost(amount=0.015)))
    res2 = await evaluator.evaluate(case, t2)
    assert res2.score == 0.0


@pytest.mark.anyio
async def test_tool_calling_evaluator():
    evaluator = ToolCallingEvaluator()

    # Success tools and matched expected
    case = GoldenTestCase(case_id="tc-1", input_query="", expected_tool_calls=["search_flights"])
    t1 = Trajectory()
    t1.add_step(
        Step(
            step_number=1,
            thought="",
            tool_calls=[ToolCall(tool_name="search_flights", arguments={}, success=True)],
        )
    )
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0

    # Failed tool
    t2 = Trajectory()
    t2.add_step(
        Step(
            step_number=1,
            thought="",
            tool_calls=[ToolCall(tool_name="search_flights", arguments={}, success=False)],
        )
    )
    res2 = await evaluator.evaluate(case, t2)
    assert res2.score == 0.0
    assert "Failed tools: search_flights" in res2.reasoning

    # Missing expected tool
    t3 = Trajectory()
    t3.add_step(
        Step(
            step_number=1,
            thought="",
            tool_calls=[ToolCall(tool_name="get_profile", arguments={}, success=True)],
        )
    )
    res3 = await evaluator.evaluate(case, t3)
    assert res3.score == 0.0
    assert "Missing expected tools: search_flights" in res3.reasoning


@pytest.mark.anyio
async def test_context_recall_evaluator():
    evaluator = ContextRecallEvaluator()

    case = GoldenTestCase(
        case_id="tc-1",
        input_query="",
        ground_truth_context=[
            "LA Cozy Inn is located in LAX",
            "United Airlines UA100 costing $250",
        ],
    )

    # Recalled all context
    t1 = Trajectory()
    t1.add_step(
        Step(
            step_number=1,
            thought="",
            observation=(
                "We found LA Cozy Inn is located in LAX. "
                "Also, United Airlines UA100 costing $250 is available."
            ),
        )
    )
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0

    # Recalled only one context item
    t2 = Trajectory()
    t2.add_step(
        Step(
            step_number=1,
            thought="",
            observation="We found LA Cozy Inn is located in LAX.",
        )
    )
    res2 = await evaluator.evaluate(case, t2)
    assert res2.score == 0.5


@pytest.mark.anyio
async def test_context_precision_evaluator():
    evaluator = ContextPrecisionEvaluator()

    case = GoldenTestCase(
        case_id="tc-1", input_query="", ground_truth_context=["UA100", "LA Cozy Inn"]
    )

    # High precision: relevant items are ranked at top
    t1 = Trajectory()
    t1.add_step(
        Step(step_number=1, thought="", observation={"flights": [{"flight_number": "UA100"}]})
    )
    t1.add_step(Step(step_number=2, thought="", observation={"hotels": [{"name": "LA Cozy Inn"}]}))
    res1 = await evaluator.evaluate(case, t1)
    assert res1.score == 1.0

    # Low precision: irrelevant items are mixed or ranked first
    t2 = Trajectory()
    t2.add_step(
        Step(
            step_number=1,
            thought="",
            observation={"attractions": [{"name": "Griffith Observatory"}]},
        )
    )
    t2.add_step(
        Step(step_number=2, thought="", observation={"flights": [{"flight_number": "UA100"}]})
    )
    res2 = await evaluator.evaluate(case, t2)
    # Rank 1: Griffith Observatory (irrelevant)
    # Rank 2: UA100 (relevant)
    # Precision@2 = 1/2 = 0.5. Average Precision = 0.5 / 1 = 0.5.
    assert res2.score == 0.5
