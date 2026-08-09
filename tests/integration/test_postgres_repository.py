import os
import asyncio
from datetime import datetime, timezone
import pytest
import psycopg2

from src.adapters.repositories.postgres_repository import PostgresEvaluationRepository
from src.domain.entities import (
    EvaluationRun,
    Experiment,
    GoldenDataset,
    GoldenTestCase,
    MetricResult,
    Step,
    TestCaseEvaluation,
    Trajectory,
)
from src.domain.value_objects import Cost, Latency, TokenUsage

# Read test DB url or default database url
DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

# Skip all tests in this file if DATABASE_URL is not set or not postgres
pytestmark = pytest.mark.skipif(
    not DATABASE_URL
    or not (DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")),
    reason="PostgreSQL database url is not configured",
)


@pytest.fixture
def clean_db():
    """Fixture to clean database before/after tests."""
    repo = PostgresEvaluationRepository(database_url=DATABASE_URL)
    # Clean up tables
    with repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE golden_datasets, evaluation_runs, experiments CASCADE")
    yield repo
    # Clean up again
    with repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE golden_datasets, evaluation_runs, experiments CASCADE")


@pytest.mark.anyio
async def test_postgres_repository_datasets(clean_db):
    repo = clean_db

    # 1. Verify initially empty
    datasets = await repo.list_datasets()
    assert len(datasets) == 0

    # 2. Save a dataset
    case1 = GoldenTestCase(
        case_id="tc-1",
        input_query="Search flights from JFK to LAX",
        expected_output="Flight UA100",
    )
    dataset1 = GoldenDataset(
        dataset_id="ds-1",
        name="Test Dataset",
        version="1.0.0",
        test_cases=[case1],
        metadata={"category": "flight"},
    )
    await repo.save_dataset(dataset1)

    # 3. Retrieve specific version
    retrieved = await repo.get_dataset("ds-1", version="1.0.0")
    assert retrieved is not None
    assert retrieved.name == "Test Dataset"
    assert len(retrieved.test_cases) == 1
    assert retrieved.test_cases[0].case_id == "tc-1"
    assert retrieved.metadata["category"] == "flight"

    # 4. Save a new version of the dataset
    case2 = GoldenTestCase(
        case_id="tc-2",
        input_query="Search hotels in CDG",
    )
    dataset2 = GoldenDataset(
        dataset_id="ds-1",
        name="Test Dataset V2",
        version="2.0.0",
        test_cases=[case1, case2],
        metadata={"category": "mixed"},
    )
    await repo.save_dataset(dataset2)

    # 5. Retrieve latest (without version arg)
    latest = await repo.get_dataset("ds-1")
    assert latest is not None
    assert latest.version == "2.0.0"
    assert latest.name == "Test Dataset V2"
    assert len(latest.test_cases) == 2

    # 6. Retrieve old version
    old = await repo.get_dataset("ds-1", version="1.0.0")
    assert old is not None
    assert old.version == "1.0.0"

    # 7. List all datasets
    all_datasets = await repo.list_datasets()
    assert len(all_datasets) == 2


@pytest.mark.anyio
async def test_postgres_repository_runs(clean_db):
    repo = clean_db

    # 1. Verify initially empty
    runs = await repo.list_runs()
    assert len(runs) == 0

    # 2. Construct and save a run
    traj = Trajectory()
    traj.add_step(
        Step(
            step_number=1,
            thought="Thinking",
            response="Done",
            token_usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            cost=Cost(amount=0.003),
            latency=Latency(seconds=1.2),
        )
    )
    case_eval = TestCaseEvaluation(
        case_id="tc-1",
        trajectory=traj,
        metrics={
            "Faithfulness": MetricResult(
                metric_name="Faithfulness", score=1.0, reasoning="Faithful"
            )
        },
        success=True,
    )
    run = EvaluationRun(
        run_id="run-101",
        dataset_id="ds-1",
        dataset_version="1.0.0",
        sut_version="v1.0.0",
        timestamp=datetime.now(timezone.utc),
        cases=[case_eval],
        parameters={"temp": 0.0},
    )
    run.compute_summary()

    await repo.save_run(run)

    # 3. Retrieve specific run
    retrieved = await repo.get_run("run-101")
    assert retrieved is not None
    assert retrieved.run_id == "run-101"
    assert retrieved.dataset_id == "ds-1"
    assert retrieved.sut_version == "v1.0.0"
    assert retrieved.summary["success_rate"] == 1.0
    assert len(retrieved.cases) == 1
    assert retrieved.cases[0].case_id == "tc-1"
    assert retrieved.cases[0].metrics["Faithfulness"].score == 1.0

    # 4. List runs
    all_runs = await repo.list_runs()
    assert len(all_runs) == 1

    # 5. List runs with filter
    filtered_runs = await repo.list_runs(dataset_id="ds-1")
    assert len(filtered_runs) == 1

    filtered_empty = await repo.list_runs(dataset_id="non-existent")
    assert len(filtered_empty) == 0


@pytest.mark.anyio
async def test_postgres_repository_transaction_rollback(clean_db):
    repo = clean_db

    # Test that transaction rolls back on failure
    try:
        with repo._get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO experiments (experiment_id, name) VALUES (%s, %s)",
                    ("exp-1", "Broken Experiment"),
                )
                # Intentionally trigger constraint error (duplicate primary key)
                cursor.execute(
                    "INSERT INTO experiments (experiment_id, name) VALUES (%s, %s)",
                    ("exp-1", "Broken Duplicate"),
                )
    except psycopg2.Error:
        pass  # expected constraint error

    # Verify that nothing was committed due to rollback
    with repo._get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM experiments")
            count = cursor.fetchone()[0]
            assert count == 0


@pytest.mark.anyio
async def test_postgres_repository_concurrency(clean_db):
    repo = clean_db

    # Concurrent inserts to ensure connection pool handles multiple concurrent requests
    async def save_run_task(i: int):
        run = EvaluationRun(
            run_id=f"run-concurrent-{i}",
            dataset_id="ds-1",
            dataset_version="1.0.0",
            sut_version="v1.0.0",
            timestamp=datetime.now(timezone.utc),
            cases=[],
            parameters={},
            summary={},
        )
        await repo.save_run(run)

    tasks = [save_run_task(i) for i in range(10)]
    await asyncio.gather(*tasks)

    all_runs = await repo.list_runs()
    assert len(all_runs) == 10
