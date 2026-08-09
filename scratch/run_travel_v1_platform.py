import asyncio
import os
import time
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    print("=== Executing travel_v1 QA Verification Run ===")
    
    # 1. Load Dataset
    loader = DatasetLoader()
    dataset = loader.load_json("datasets/travel_v1.json")
    print(f"Loaded travel_v1 dataset with {len(dataset.test_cases)} cases.")
    
    # 2. Setup Components
    sut = TravelAgentSUT()
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    database_url = os.getenv("DATABASE_URL")
    if database_url and (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
        from src.adapters.repositories.postgres_repository import PostgresEvaluationRepository
        repo = PostgresEvaluationRepository(database_url=database_url)
        print("Using Postgres database for execution.")
    else:
        repo = SqliteEvaluationRepository("evalforge_platform.db")
        print("Using SQLite database for execution.")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    evaluators = list(registry.list_evaluators())
    
    # 3. Save dataset to registry
    await repo.save_dataset(dataset)
    
    # 4. Configure BenchmarkConfig
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock Mode)",
        evaluators=evaluators,
        concurrency=5,  # Speedup
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    run_id = "run-platform-travel-v1"
    print(f"Running evaluation suite. Run ID: {run_id} ...")
    
    start_time = time.perf_counter()
    run = await runner.run_benchmark(run_id=run_id, config=config, sut=sut)
    duration = time.perf_counter() - start_time
    
    # 5. Verify and Print Summary
    print(f"Benchmark finished in {duration:.2f}s.")
    print(f"Total Cases: {run.summary.get('total_cases')}")
    print(f"Successful Cases: {run.summary.get('successful_cases')}")
    print(f"Success Rate: {run.summary.get('success_rate') * 100:.1f}%")
    
    # Verify PAss/Fail details
    for case in run.cases:
        print(f"Case {case.case_id}: {'PASS' if case.success else 'FAIL'}")
        if not case.success:
            for name, m_res in case.metrics.items():
                print(f"  Metric: {name} | Score: {m_res.score} | Reason: {m_res.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
