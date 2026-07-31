import asyncio
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    loader = DatasetLoader()
    dataset = loader.load_json("datasets/travel_v1.json")
    
    # Isolate to just the first test case
    dataset.test_cases = dataset.test_cases[:1]
    case = dataset.test_cases[0]
    print(f"Case ID: {case.case_id}")
    print(f"  User Query: {case.user_query}")
    print(f"  Expected Answer: {case.expected_answer}")
    print(f"  Constraints: {case.constraints}")
    print(f"  Expected Metrics: {case.expected_metrics}")
    print(f"  Expected Judge Scores: {case.expected_judge_scores}")
    
    sut = TravelAgentSUT()
    # We use mock mode = True for instant response
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    
    repo = SqliteEvaluationRepository("evalforge_platform_trace.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    
    evaluators = list(registry.list_evaluators())
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock)",
        evaluators=evaluators,
        concurrency=1,
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    print("\nRunning single case benchmark evaluation...")
    run = await runner.run_benchmark(run_id="run-trace-v1-001", config=config, sut=sut)
    
    print("\nBenchmark Run completed!")
    print(f"  Run ID: {run.run_id}")
    print(f"  Success Rate: {run.summary.get('success_rate')}")
    print(f"  Successful Cases: {run.summary.get('successful_cases')}/{run.summary.get('total_cases')}")
    
    saved_run = await repo.get_run(run.run_id)
    case_eval = saved_run.cases[0]
    print(f"\nCase Evaluation Result:")
    print(f"  Success: {case_eval.success}")
    print(f"  Metrics:")
    for m_name, m_res in case_eval.metrics.items():
        print(f"    {m_name}: score={m_res.score}, reasoning={m_res.reasoning}")

if __name__ == "__main__":
    asyncio.run(main())
