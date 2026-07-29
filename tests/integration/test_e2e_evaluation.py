import pytest

from examples.travel_agent.travel_agent_sut import TravelAgentSUT
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.domain.entities import GoldenDataset, GoldenTestCase, MetricResult, Trajectory
from src.domain.interfaces.evaluator import BaseEvaluator
from src.use_cases.runners.benchmark_runner import BenchmarkRunner


class SimpleMockEvaluator(BaseEvaluator):
    """Simple evaluator that returns a fixed score for testing."""

    def __init__(self, name: str, score: float):
        self._name = name
        self.score = score

    @property
    def name(self) -> str:
        return self._name

    async def evaluate(self, test_case: GoldenTestCase, trajectory: Trajectory) -> MetricResult:
        # Check that we can access trajectory steps and response
        assert len(trajectory.steps) > 0
        return MetricResult(
            metric_name=self.name,
            score=self.score,
            reasoning=f"Mock evaluation for {self.name}",
        )


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "e2e_evalforge.db")


@pytest.mark.anyio
async def test_e2e_evaluation_pipeline(db_path):
    # 1. Initialize SQLite Repository
    repo = SqliteEvaluationRepository(db_path=db_path)

    # 2. Define Golden Test Cases
    cases = [
        GoldenTestCase(
            case_id="tc-e2e-1",
            input_query="Book a flight from JFK to LAX on 2026-08-01 for user U101 in Economy",
            expected_output="Flight UA100",
            expected_tool_calls=[
                "get_profile",
                "search_flights",
                "search_hotels",
                "validate_booking",
            ],
        ),
        GoldenTestCase(
            case_id="tc-e2e-2",
            input_query="What is the weather forecast for Paris on 2026-08-05?",
            expected_output="Partly Cloudy",
            expected_tool_calls=["get_weather"],
        ),
        GoldenTestCase(
            case_id="tc-e2e-3",
            input_query="Convert 150 EUR to USD",
            expected_output="163.04",
            expected_tool_calls=["convert_currency"],
        ),
        GoldenTestCase(
            case_id="tc-e2e-4",
            input_query="What attractions can I visit in CDG?",
            expected_output="Eiffel Tower",
            expected_tool_calls=["get_attractions"],
        ),
        GoldenTestCase(
            case_id="tc-e2e-5",
            input_query="Book a business flight from JFK to LAX on 2026-08-01 for user U101",
            expected_output="violates travel policy guidelines",
            expected_tool_calls=[
                "get_profile",
                "search_flights",
                "search_hotels",
                "validate_booking",
            ],
        ),
    ]

    dataset = GoldenDataset(
        dataset_id="ds-e2e-travel",
        name="E2E Travel Agent Benchmark Dataset",
        version="1.0.0",
        test_cases=cases,
    )

    # Save dataset to repository
    await repo.save_dataset(dataset)

    # 3. Instantiate TravelAgentSUT
    sut = TravelAgentSUT()

    # 4. Instantiate Registry and Evaluators
    from src.use_cases.metrics.registry import MetricRegistry

    registry = MetricRegistry()
    registry.register(SimpleMockEvaluator("Faithfulness", 1.0))
    registry.register(SimpleMockEvaluator("Groundedness", 0.9))

    # 5. Run Benchmark
    runner = BenchmarkRunner(repository=repo, registry=registry)
    run_id = "run-e2e-test-100"

    evaluation_run = await runner.run_evaluation(
        run_id=run_id,
        dataset=dataset,
        sut=sut,
        max_concurrency=3,
        parameters={"test_mode": "integration-e2e"},
    )

    # 6. Verify Evaluation Results
    assert evaluation_run.run_id == run_id
    assert evaluation_run.dataset_id == "ds-e2e-travel"
    assert evaluation_run.sut_version == sut.version
    assert len(evaluation_run.cases) == 5

    # All cases should succeed since the SUT ran successfully and evaluators scored >= 0.5
    assert evaluation_run.summary["total_cases"] == 5
    assert evaluation_run.summary["successful_cases"] == 5
    assert evaluation_run.summary["success_rate"] == 1.0
    assert evaluation_run.summary["avg_metrics"]["Faithfulness"] == 1.0
    assert evaluation_run.summary["avg_metrics"]["Groundedness"] == 0.9
    assert evaluation_run.summary["total_tokens"] > 0
    assert evaluation_run.summary["total_cost"] > 0
    assert evaluation_run.summary["avg_latency"] >= 0

    # 7. Check persistence in SQLite
    saved_run = await repo.get_run(run_id)
    assert saved_run is not None
    assert saved_run.run_id == run_id
    assert len(saved_run.cases) == 5
    assert saved_run.summary["success_rate"] == 1.0

    # Ensure dataset is listed correctly
    datasets = await repo.list_datasets()
    assert len(datasets) == 1
    assert datasets[0].dataset_id == "ds-e2e-travel"

    # Ensure runs are listed correctly
    runs = await repo.list_runs()
    assert len(runs) == 1
    assert runs[0].run_id == run_id
