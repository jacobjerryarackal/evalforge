import asyncio
import logging
from datetime import datetime, timezone
from typing import Sequence

from src.domain.entities import (
    BenchmarkConfig,
    EvaluationRun,
    GoldenDataset,
    GoldenTestCase,
    MetricResult,
    RetryPolicy,
    Step,
    TestCaseEvaluation,
    Trajectory,
)
from src.domain.interfaces.evaluator import BaseEvaluator
from src.domain.interfaces.repository import EvaluationRepository
from src.domain.interfaces.sut import AgentSUT
from src.domain.value_objects import Latency
from src.use_cases.metrics.aggregation import AggregationEngine
from src.use_cases.metrics.registry import MetricRegistry

logger = logging.getLogger("evaluation.benchmark_runner")


class BenchmarkRunner:
    """Orchestrator for executing evaluation runs on a GoldenDataset using an AgentSUT."""

    def __init__(
        self,
        repository: EvaluationRepository,
        registry: MetricRegistry,
        metric_names: Sequence[str] | None = None,
        aggregation_engine: AggregationEngine | None = None,
    ):
        """Initializes the runner with storage repository, metric registry and aggregator."""
        self.repository = repository
        self.registry = registry
        self.metric_names = metric_names
        self.aggregation_engine = aggregation_engine or AggregationEngine()

    async def run_evaluation(
        self,
        run_id: str,
        dataset: GoldenDataset,
        sut: AgentSUT,
        max_concurrency: int = 3,
        parameters: dict | None = None,
    ) -> EvaluationRun:
        """Runs the benchmark suite on the given dataset using the target agent SUT.

        Maintained for backward compatibility. Wraps parameters in BenchmarkConfig
        and calls run_benchmark.
        """
        config = BenchmarkConfig(
            dataset=dataset,
            provider="unknown",
            evaluators=list(self.metric_names) if self.metric_names else [],
            concurrency=max_concurrency,
            retry_policy=RetryPolicy(max_retries=0),
            execution_parameters=parameters or {},
        )
        return await self.run_benchmark(run_id, config, sut)

    async def run_benchmark(
        self,
        run_id: str,
        config: BenchmarkConfig,
        sut: AgentSUT,
    ) -> EvaluationRun:
        """Runs the benchmark suite using a centralized BenchmarkConfig."""
        logger.info(
            f"Starting benchmark run {run_id} | Dataset: {config.dataset.dataset_id} "
            f"(v{config.dataset.version}) | SUT: {sut.version} | Concurrency: {config.concurrency}"
        )

        semaphore = asyncio.Semaphore(config.concurrency)
        tasks = [
            self._evaluate_case_bounded(case, sut, semaphore, config)
            for case in config.dataset.test_cases
        ]

        # Run all test cases with bounded concurrency
        case_evaluations = await asyncio.gather(*tasks)

        # Build the final run results
        run = EvaluationRun(
            run_id=run_id,
            dataset_id=config.dataset.dataset_id,
            dataset_version=config.dataset.version,
            sut_version=sut.version,
            timestamp=datetime.now(timezone.utc),
            cases=list(case_evaluations),
            parameters=config.execution_parameters,
        )

        # Calculate aggregations and summary via AggregationEngine
        run.summary = self.aggregation_engine.aggregate(run.cases)

        # Persist run results
        await self.repository.save_run(run)
        success_rate = run.summary.get("success_rate", 0.0)
        logger.info(
            f"Benchmark run {run_id} completed and stored. Success rate: {success_rate:.2%}"
        )

        return run

    async def _evaluate_case_bounded(
        self,
        case: GoldenTestCase,
        sut: AgentSUT,
        semaphore: asyncio.Semaphore,
        config: BenchmarkConfig | None = None,
    ) -> TestCaseEvaluation:
        """Acquires the concurrency semaphore and evaluates a single test case."""
        async with semaphore:
            return await self._evaluate_case(case, sut, config)

    async def _evaluate_case(
        self,
        case: GoldenTestCase,
        sut: AgentSUT,
        config: BenchmarkConfig | None = None,
    ) -> TestCaseEvaluation:
        """Executes the SUT on the test case, runs all evaluators, and checks thresholds."""
        logger.info(f"Executing case {case.case_id}: {case.input_query[:40]}...")
        start_time = datetime.now(timezone.utc)

        if config is None:
            config = BenchmarkConfig(
                dataset=GoldenDataset(dataset_id="unknown", name="unknown", test_cases=[case]),
                provider="unknown",
                evaluators=list(self.metric_names) if self.metric_names else [],
                retry_policy=RetryPolicy(max_retries=0),
            )

        # 1. Run the agent SUT and capture trajectory with retry loop
        sut_failed = False
        trajectory = Trajectory()

        max_retries = config.retry_policy.max_retries
        delay = config.retry_policy.initial_delay
        backoff_factor = config.retry_policy.backoff_factor

        for attempt in range(max_retries + 1):
            try:
                trajectory = await sut.run(case.input_query)
                sut_failed = False
                break
            except Exception as e:
                sut_failed = True
                logger.warning(
                    f"SUT execution attempt {attempt + 1}/{max_retries + 1} "
                    f"failed on case {case.case_id}: {e}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
                else:
                    logger.error(
                        f"SUT crashed on case {case.case_id} after {max_retries + 1} attempts: {e}",
                        exc_info=True,
                    )
                    # Create a failed trajectory with a terminal error step
                    trajectory = Trajectory()
                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                    trajectory.add_step(
                        Step(
                            step_number=1,
                            thought="SUT execution failed with an unhandled exception.",
                            metadata={"error": str(e), "exception_type": type(e).__name__},
                            latency=Latency(seconds=duration),
                        )
                    )

        # 2. Run all selected metrics concurrently on the generated trajectory
        names_to_run = (
            config.evaluators
            if config.evaluators
            else (self.metric_names or self.registry.list_evaluators())
        )
        evaluator_tasks = [
            self._safe_evaluate(self.registry.get(name), case, trajectory) for name in names_to_run
        ]

        metric_results_list = await asyncio.gather(*evaluator_tasks)
        metrics = {res.metric_name: res for res in metric_results_list}

        # 3. Determine overall success based on metric thresholds and SUT execution status
        # Rule: A case succeeds if SUT execution was successful and all
        # metric results are boolean True or (if numeric) >= 0.5.
        success = not sut_failed
        if success:
            for m_res in metrics.values():
                if m_res.score is False:
                    success = False
                    break
                if isinstance(m_res.score, (int, float)) and m_res.score < 0.5:
                    success = False
                    break

        return TestCaseEvaluation(
            case_id=case.case_id,
            trajectory=trajectory,
            metrics=metrics,
            success=success,
            evaluated_at=datetime.now(timezone.utc),
        )

    async def _safe_evaluate(
        self,
        evaluator: BaseEvaluator,
        case: GoldenTestCase,
        trajectory: Trajectory,
    ) -> MetricResult:
        """Executes a single evaluator safely, shielding the runner from evaluator failures."""
        try:
            return await evaluator.evaluate(case, trajectory)
        except Exception as e:
            logger.error(
                f"Evaluator {evaluator.name} failed on case {case.case_id}: {e}", exc_info=True
            )
            return MetricResult(
                metric_name=evaluator.name,
                score=0.0,
                reasoning=f"Evaluator failed with exception: {str(e)}",
                metadata={"error": str(e), "exception_type": type(e).__name__},
            )
