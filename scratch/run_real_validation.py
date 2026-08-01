import asyncio
import os
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    print("=== Running Real Validation for travel_v1 ===")
    
    loader = DatasetLoader()
    sut = TravelAgentSUT()
    
    # Initialize real provider (will read GEMINI_API_KEY from env)
    provider = GeminiProvider(mock_mode=False)
    registry = create_default_registry(provider)
    repo = SqliteEvaluationRepository("evalforge_real_validation.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    evaluators = list(registry.list_evaluators())
    
    dataset = loader.load_json("datasets/travel_v1.json")
    
    # Run first 5 cases to verify speed and correctness
    dataset.test_cases = dataset.test_cases[:5]
    
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Real)",
        evaluators=evaluators,
        concurrency=2,
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    run = await runner.run_benchmark(run_id="run-real-travel-v1", config=config, sut=sut)
    
    passed_count = sum(1 for c in run.cases if c.success)
    print(f"\nResults: {passed_count} / {len(run.cases)} Passed")
    for case in run.cases:
        print(f"Case {case.case_id} success: {case.success}")
        for name, m_res in case.metrics.items():
            print(f"  Metric: {name} | Score: {m_res.score} | Reason: {m_res.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
