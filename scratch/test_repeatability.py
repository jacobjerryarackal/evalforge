import asyncio
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    print("=== EvalForge Repeatability Audit ===")
    loader = DatasetLoader()
    dataset = loader.load_json("datasets/travel_v1.json")
    
    # Run the first 5 cases to keep the audit concise and thorough
    dataset.test_cases = dataset.test_cases[:5]
    
    sut = TravelAgentSUT()
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    repo = SqliteEvaluationRepository("evalforge_platform_repeatability.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    evaluators = list(registry.list_evaluators())
    
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock)",
        evaluators=evaluators,
        concurrency=1,
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    run_results = []
    for iteration in range(1, 4):
        run_id = f"run-repeatability-{iteration}"
        print(f"\nExecution Run {iteration}/3 ({run_id})...")
        run = await runner.run_benchmark(run_id=run_id, config=config, sut=sut)
        
        # Load from repo to verify database persistence
        saved_run = await repo.get_run(run_id)
        run_results.append(saved_run)
        print(f"  Success Rate: {saved_run.summary.get('success_rate') * 100:.2f}% ({saved_run.summary.get('successful_cases')}/{saved_run.summary.get('total_cases')})")

    # Verify determinism across executions
    print("\n--- Verifying Case-by-Case Consistency ---")
    mismatches = 0
    for idx, case in enumerate(dataset.test_cases):
        case_id = case.case_id
        scores_run1 = {m_name: m_res.score for m_name, m_res in run_results[0].cases[idx].metrics.items()}
        scores_run2 = {m_name: m_res.score for m_name, m_res in run_results[1].cases[idx].metrics.items()}
        scores_run3 = {m_name: m_res.score for m_name, m_res in run_results[2].cases[idx].metrics.items()}
        
        success1 = run_results[0].cases[idx].success
        success2 = run_results[1].cases[idx].success
        success3 = run_results[2].cases[idx].success
        
        is_consistent_success = (success1 == success2 == success3)
        is_consistent_scores = (scores_run1 == scores_run2 == scores_run3)
        
        status = "CONSISTENT" if (is_consistent_success and is_consistent_scores) else "MISMATCH"
        print(f"Case {case_id}: Success Status Consistency={is_consistent_success}, Metrics Scores Consistency={is_consistent_scores} -> {status}")
        
        if not (is_consistent_success and is_consistent_scores):
            mismatches += 1
            print(f"  Run 1: Success={success1}, Scores={scores_run1}")
            print(f"  Run 2: Success={success2}, Scores={scores_run2}")
            print(f"  Run 3: Success={success3}, Scores={scores_run3}")
            
    print(f"\nRepeatability Check Complete. Total Mismatches: {mismatches}")

if __name__ == "__main__":
    asyncio.run(main())
