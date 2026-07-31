import asyncio
from src.domain.entities.dataset import GoldenDataset, GoldenTestCase
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    # Define a test case with loose constraints that the mock SUT can easily satisfy
    case = GoldenTestCase(
        id="travel_v1_passing_test",
        difficulty="Easy",
        category="flight",
        user_query="I need a flight from New York to London.",
        retrieved_context="Flight UA100 operates daily between JFK and LAX.",
        expected_answer="Mock final response",
        latency_constraint=10.0,    # Very loose
        token_constraint=2000,      # Mock SUT uses ~398, so it will pass
        cost_constraint=0.50,       # Mock SUT costs ~$0.01, so it will pass
        expected_metrics={
            "context_precision": 0.1,  # Mock SUT gets 0.33, so it will pass
            "context_recall": 0.5      # Mock SUT gets 1.0, so it will pass
        },
        expected_judge_scores={
            "faithfulness": 0.5,       # Mock judge returns 0.8, so it will pass
            "groundedness": 0.5,       # Mock judge returns 0.8, so it will pass
            "correctness": 0.5,        # Mock judge returns 0.8, so it will pass
            "hallucination": 1.0       # Mock judge returns 0.0, which is <= 1.0, so it will pass
        }
    )
    
    dataset = GoldenDataset(
        dataset_id="travel_passing_ds",
        name="Passing Test Dataset",
        version="1.0.0",
        test_cases=[case]
    )
    
    sut = TravelAgentSUT()
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    repo = SqliteEvaluationRepository("evalforge_platform_passing_test.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    
    evaluators = list(registry.list_evaluators())
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock)",
        evaluators=evaluators,
        concurrency=1,
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    print("Running passing case benchmark evaluation...")
    run = await runner.run_benchmark(run_id="run-passing-test-101", config=config, sut=sut)
    
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
        print(f"    {m_name}: score={m_res.score}, threshold comparison status: "
              f"expected={case.expected_metrics.get(m_name.lower()) or case.expected_judge_scores.get(m_name.lower()) or '0.5'}")

if __name__ == "__main__":
    asyncio.run(main())
