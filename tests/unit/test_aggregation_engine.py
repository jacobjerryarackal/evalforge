from datetime import datetime, timezone

from src.domain.entities import MetricResult, Step, TestCaseEvaluation, Trajectory
from src.domain.value_objects import Cost, Latency, TokenUsage
from src.use_cases.metrics.aggregation import AggregationEngine


def test_aggregation_engine_empty():
    engine = AggregationEngine()
    summary = engine.aggregate([])
    assert summary["total_cases"] == 0
    assert summary["success_rate"] == 0.0
    assert summary["avg_latency"] == 0.0
    assert summary["total_cost"] == 0.0
    assert summary["total_tokens"] == 0


def test_aggregation_engine_calculations():
    engine = AggregationEngine()

    # Case 1
    t1 = Trajectory()
    t1.add_step(
        Step(
            step_number=1,
            thought="Step 1",
            latency=Latency(seconds=1.5),
            cost=Cost(amount=0.002),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )
    )
    case_eval1 = TestCaseEvaluation(
        case_id="c1",
        trajectory=t1,
        metrics={
            "Latency": MetricResult(metric_name="Latency", score=1.0),
            "Faithfulness": MetricResult(metric_name="Faithfulness", score=0.8),
        },
        success=True,
        evaluated_at=datetime.now(timezone.utc),
    )

    # Case 2
    t2 = Trajectory()
    t2.add_step(
        Step(
            step_number=1,
            thought="Step 1",
            latency=Latency(seconds=2.5),
            cost=Cost(amount=0.003),
            token_usage=TokenUsage(prompt_tokens=15, completion_tokens=25, total_tokens=40),
        )
    )
    case_eval2 = TestCaseEvaluation(
        case_id="c2",
        trajectory=t2,
        metrics={
            "Latency": MetricResult(metric_name="Latency", score=0.0),
            "Faithfulness": MetricResult(metric_name="Faithfulness", score=0.6),
        },
        success=False,
        evaluated_at=datetime.now(timezone.utc),
    )

    summary = engine.aggregate([case_eval1, case_eval2])

    assert summary["total_cases"] == 2
    assert summary["successful_cases"] == 1
    assert summary["success_rate"] == 0.5
    assert summary["avg_latency"] == 2.0  # (1.5 + 2.5) / 2
    assert summary["total_cost"] == 0.005  # 0.002 + 0.003
    assert summary["total_tokens"] == 70  # 30 + 40
    assert summary["avg_metrics"]["Latency"] == 0.5  # (1.0 + 0.0) / 2
    assert summary["avg_metrics"]["Faithfulness"] == 0.7  # (0.8 + 0.6) / 2
