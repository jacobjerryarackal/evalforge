
import pytest
from pydantic import ValidationError

from src.domain.entities import (
    EvaluationRun,
    GoldenDataset,
    GoldenTestCase,
    MetricResult,
    Step,
    TestCaseEvaluation,
    ToolCall,
    Trajectory,
)
from src.domain.value_objects import Cost, Latency, TokenUsage


def test_token_usage_addition():
    u1 = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    u2 = TokenUsage(prompt_tokens=20, completion_tokens=15, total_tokens=35)

    result = u1 + u2
    assert result.prompt_tokens == 30
    assert result.completion_tokens == 20
    assert result.total_tokens == 50

    # Verify immutability
    with pytest.raises(ValidationError):
        # Pydantic v2 raises ValidationError when trying to set an attribute of a frozen model
        u1.prompt_tokens = 15


def test_cost_addition():
    c1 = Cost(amount=0.05, currency="USD")
    c2 = Cost(amount=0.10, currency="USD")

    result = c1 + c2
    assert result.amount == pytest.approx(0.15)
    assert result.currency == "USD"

    c_eur = Cost(amount=0.10, currency="EUR")
    with pytest.raises(ValueError, match="Cannot add costs with different currencies"):
        _ = c1 + c_eur


def test_latency_addition():
    l1 = Latency(seconds=1.5)
    l2 = Latency(seconds=2.2)
    result = l1 + l2
    assert result.seconds == pytest.approx(3.7)


def test_trajectory_add_step():
    traj = Trajectory()
    assert len(traj.steps) == 0
    assert traj.total_token_usage.total_tokens == 0
    assert traj.total_cost.amount == 0.0
    assert traj.total_latency.seconds == 0.0

    step1 = Step(
        step_number=1,
        thought="Searching for hotels in Tokyo...",
        tool_calls=[ToolCall(tool_name="hotel_search", arguments={"city": "Tokyo"}, success=True)],
        token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        cost=Cost(amount=0.002),
        latency=Latency(seconds=1.2),
    )

    traj.add_step(step1)
    assert len(traj.steps) == 1
    assert traj.total_token_usage.total_tokens == 150
    assert traj.total_cost.amount == pytest.approx(0.002)
    assert traj.total_latency.seconds == pytest.approx(1.2)
    assert traj.final_response is None

    step2 = Step(
        step_number=2,
        thought="Found Tokyo Bay Hotel.",
        response="I recommend the Tokyo Bay Hotel.",
        token_usage=TokenUsage(prompt_tokens=150, completion_tokens=100, total_tokens=250),
        cost=Cost(amount=0.004),
        latency=Latency(seconds=1.5),
    )

    traj.add_step(step2)
    assert len(traj.steps) == 2
    assert traj.total_token_usage.total_tokens == 400
    assert traj.total_cost.amount == pytest.approx(0.006)
    assert traj.total_latency.seconds == pytest.approx(2.7)
    assert traj.final_response == "I recommend the Tokyo Bay Hotel."
    assert len(traj.all_tool_calls) == 1
    assert traj.all_tool_calls[0].tool_name == "hotel_search"


def test_golden_dataset_get_case():
    case1 = GoldenTestCase(
        case_id="tc-1",
        input_query="Find boutique hotels in Kyoto",
        expected_output="Kyoto Boutique Inn",
        ground_truth_context=["Kyoto Boutique Inn is a 5-star hotel in Kyoto."],
        expected_tool_calls=["hotel_search"],
    )
    case2 = GoldenTestCase(
        case_id="tc-2",
        input_query="Find flights to Rome",
        expected_output="Flight AZ123",
        ground_truth_context=["Flight AZ123 leaves Rome at 10 AM."],
        expected_tool_calls=["flight_search"],
    )

    dataset = GoldenDataset(
        dataset_id="ds-1",
        name="Travel Agent Golden Dataset",
        version="1.0.0",
        test_cases=[case1, case2],
    )

    assert dataset.get_case("tc-1") == case1
    assert dataset.get_case("tc-2") == case2
    assert dataset.get_case("non-existent") is None


def test_evaluation_run_compute_summary():
    run = EvaluationRun(
        run_id="run-1",
        dataset_id="ds-1",
        dataset_version="1.0.0",
        sut_version="v0.1.0",
    )

    assert not run.cases
    run.compute_summary()
    assert run.summary["total_cases"] == 0

    traj1 = Trajectory()
    traj1.add_step(
        Step(
            step_number=1,
            response="Answer 1",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            cost=Cost(amount=0.01),
            latency=Latency(seconds=1.0),
        )
    )

    case_eval1 = TestCaseEvaluation(
        case_id="tc-1",
        trajectory=traj1,
        metrics={
            "Faithfulness": MetricResult(
                metric_name="Faithfulness", score=1.0, reasoning="Fully faithful"
            ),
            "Groundedness": MetricResult(
                metric_name="Groundedness", score=0.8, reasoning="Mostly grounded"
            ),
        },
        success=True,
    )

    traj2 = Trajectory()
    traj2.add_step(
        Step(
            step_number=1,
            response="Answer 2",
            token_usage=TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300),
            cost=Cost(amount=0.02),
            latency=Latency(seconds=2.0),
        )
    )

    case_eval2 = TestCaseEvaluation(
        case_id="tc-2",
        trajectory=traj2,
        metrics={
            "Faithfulness": MetricResult(
                metric_name="Faithfulness", score=0.0, reasoning="Contains hallucinations"
            ),
            "Groundedness": MetricResult(
                metric_name="Groundedness", score=0.2, reasoning="Poorly grounded"
            ),
        },
        success=False,
    )

    run.cases = [case_eval1, case_eval2]
    run.compute_summary()

    assert run.summary["total_cases"] == 2
    assert run.summary["successful_cases"] == 1
    assert run.summary["success_rate"] == 0.5
    assert run.summary["avg_latency"] == pytest.approx(1.5)
    assert run.summary["total_cost"] == pytest.approx(0.03)
    assert run.summary["total_tokens"] == 450
    assert run.summary["avg_metrics"]["Faithfulness"] == pytest.approx(0.5)
    assert run.summary["avg_metrics"]["Groundedness"] == pytest.approx(0.5)
