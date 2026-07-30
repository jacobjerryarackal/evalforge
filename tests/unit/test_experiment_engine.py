from datetime import datetime, timezone

import pytest

from src.adapters.repositories import InMemoryEvaluationRepository, SqliteEvaluationRepository
from src.domain import (
    Cost,
    EvaluationRun,
    Experiment,
    Latency,
    MetricResult,
    Step,
    TestCaseEvaluation,
    TokenUsage,
    Trajectory,
)
from src.use_cases.experiments.engine import (
    ExperimentComparer,
    ExperimentEngine,
    ExperimentSummaryGenerator,
)


def _create_mock_run(
    run_id: str,
    sut_version: str,
    success_rate: float,
    latency: float,
    cost: float,
    tokens: int,
    faithfulness_score: float,
) -> EvaluationRun:
    """Helper to construct an EvaluationRun with specific metrics and trajectory details."""
    traj = Trajectory()
    traj.add_step(
        Step(
            step_number=1,
            response="Mock response",
            token_usage=TokenUsage(
                prompt_tokens=int(tokens * 0.6),
                completion_tokens=int(tokens * 0.4),
                total_tokens=tokens,
            ),
            cost=Cost(amount=cost),
            latency=Latency(seconds=latency),
        )
    )

    case_eval = TestCaseEvaluation(
        case_id="tc-1",
        trajectory=traj,
        metrics={
            "Faithfulness": MetricResult(
                metric_name="Faithfulness", score=faithfulness_score, reasoning="Mock score"
            )
        },
        success=success_rate > 0.5,
        evaluated_at=datetime.now(timezone.utc),
    )

    run = EvaluationRun(
        run_id=run_id,
        dataset_id="ds-test",
        dataset_version="1.0.0",
        sut_version=sut_version,
        timestamp=datetime.now(timezone.utc),
        cases=[case_eval],
        parameters={},
    )
    run.compute_summary()
    return run


def test_experiment_comparer_deltas():
    # Construct run A (baseline) and run B
    run_a = _create_mock_run(
        run_id="run-a",
        sut_version="v1.0.0",
        success_rate=1.0,
        latency=2.0,
        cost=0.01,
        tokens=1000,
        faithfulness_score=0.9,
    )
    run_b = _create_mock_run(
        run_id="run-b",
        sut_version="v1.1.0",
        success_rate=1.0,
        latency=1.5,
        cost=0.008,
        tokens=800,
        faithfulness_score=0.95,
    )

    comparison = ExperimentComparer.compare_runs([run_a, run_b])

    assert len(comparison) == 2
    assert "run-a" in comparison
    assert "run-b" in comparison

    # Baseline run has empty deltas
    assert comparison["run-a"]["deltas"] == {}

    # Run B has calculated deltas relative to baseline Run A
    deltas_b = comparison["run-b"]["deltas"]
    assert deltas_b["success_rate"] == 0.0
    assert deltas_b["avg_latency"] == pytest.approx(-0.5)
    assert deltas_b["total_cost"] == pytest.approx(-0.002)
    assert deltas_b["total_tokens"] == -200
    assert deltas_b["avg_metrics"]["Faithfulness"] == pytest.approx(0.05)


def test_experiment_summary_report():
    run_a = _create_mock_run(
        run_id="run-a",
        sut_version="v1.0.0",
        success_rate=0.0,  # Fails
        latency=2.0,
        cost=0.01,
        tokens=1000,
        faithfulness_score=0.4,
    )
    run_b = _create_mock_run(
        run_id="run-b",
        sut_version="v1.1.0",
        success_rate=1.0,  # Succeeds
        latency=1.5,
        cost=0.008,
        tokens=800,
        faithfulness_score=0.95,
    )

    experiment = Experiment(
        experiment_id="exp-1",
        name="Mock Prompt Optimization",
        description="Comparing system prompt v1 and v2",
        runs=[run_a, run_b],
    )

    summary = ExperimentSummaryGenerator.generate_markdown_summary(experiment)

    assert "# Experiment: Mock Prompt Optimization" in summary
    assert "**Best Run Config**: `run-b`" in summary
    assert "Comparing system prompt v1 and v2" in summary
    assert "| `run-a` |" in summary
    assert "| `run-b` |" in summary
    assert "Faithfulness**: 0.9500" in summary
    assert "Performance Deltas (vs. Baseline Run)" in summary


@pytest.mark.asyncio
async def test_experiment_engine_lifecycle_in_memory():
    repo = InMemoryEvaluationRepository()
    engine = ExperimentEngine(repository=repo)

    # 1. Create experiment
    exp = await engine.create_experiment(
        experiment_id="exp-lifecycle",
        name="Travel Agent Evaluation",
        description="Testing different model backends",
        metadata={"category": "travel"},
    )
    assert exp.experiment_id == "exp-lifecycle"
    assert exp.name == "Travel Agent Evaluation"
    assert exp.description == "Testing different model backends"

    # 2. Add run to experiment
    run = _create_mock_run(
        run_id="run-life",
        sut_version="v1.0.0",
        success_rate=1.0,
        latency=1.0,
        cost=0.001,
        tokens=200,
        faithfulness_score=1.0,
    )
    # Save the run in repository first
    # (as engine expects runs to exist or will store them in experiment)
    await repo.save_run(run)

    updated_exp = await engine.add_run_to_experiment("exp-lifecycle", run)
    assert len(updated_exp.runs) == 1
    assert updated_exp.runs[0].run_id == "run-life"

    # 3. Retrieve experiment
    fetched = await engine.get_experiment("exp-lifecycle")
    assert fetched is not None
    assert fetched.name == "Travel Agent Evaluation"
    assert len(fetched.runs) == 1

    # 4. List experiments
    all_exps = await engine.list_experiments()
    assert len(all_exps) == 1
    assert all_exps[0].experiment_id == "exp-lifecycle"


@pytest.mark.asyncio
async def test_experiment_persistence_sqlite(tmp_path):
    db_file = tmp_path / "test_evalforge.db"
    repo = SqliteEvaluationRepository(db_path=str(db_file))

    # Initialize experiment & runs
    run = _create_mock_run(
        run_id="run-sqlite",
        sut_version="v1.0.0",
        success_rate=1.0,
        latency=1.0,
        cost=0.001,
        tokens=200,
        faithfulness_score=1.0,
    )
    # Save the run first because SQLite references it
    await repo.save_run(run)

    exp = Experiment(
        experiment_id="exp-sqlite",
        name="SQLite Experiment",
        description="Testing SQLite storage",
        runs=[run],
        metadata={"db": "sqlite"},
    )

    # Save
    await repo.save_experiment(exp)

    # Get
    fetched = await repo.get_experiment("exp-sqlite")
    assert fetched is not None
    assert fetched.experiment_id == "exp-sqlite"
    assert fetched.name == "SQLite Experiment"
    assert fetched.description == "Testing SQLite storage"
    assert fetched.metadata["db"] == "sqlite"
    assert len(fetched.runs) == 1
    assert fetched.runs[0].run_id == "run-sqlite"

    # List
    all_exps = await repo.list_experiments()
    assert len(all_exps) == 1
    assert all_exps[0].experiment_id == "exp-sqlite"
