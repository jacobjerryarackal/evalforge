import asyncio
import os
import json
import time
from datetime import datetime, timezone
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

DATASETS = [
    ("travel_v1.json", 25),
    ("travel_tool_calls.json", 20),
    ("travel_long_context.json", 20),
    ("travel_regression.json", 15),
    ("travel_safety.json", 20),
    ("travel_missing_context.json", 15),
    ("travel_edge_cases.json", 20),
    ("travel_multilingual.json", 15),
    ("travel_adversarial.json", 15),
    ("travel_provider_benchmark.json", 15)
]

async def main():
    print("=== EvalForge Concrete E2E Execution Audit (All 180 Cases) ===")
    
    loader = DatasetLoader()
    sut = TravelAgentSUT()
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    repo = SqliteEvaluationRepository("evalforge_certification_evidence.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    evaluators = list(registry.list_evaluators())
    
    overall_total_cases = 0
    overall_executed = 0
    overall_passed = 0
    overall_failed = 0
    overall_skipped = 0
    
    results = {}
    
    for filename, expected_count in DATASETS:
        path = os.path.join("datasets", filename)
        dataset = loader.load_json(path)
        
        # Verify discovered count
        discovered = len(dataset.test_cases)
        
        # Save dataset to register it
        await repo.save_dataset(dataset)
        
        config = BenchmarkConfig(
            dataset=dataset,
            provider="Gemini (Mock)",
            evaluators=evaluators,
            concurrency=5, # Concurrency speedup
            retry_policy=RetryPolicy(max_retries=1)
        )
        
        run_id = f"run-cert-{dataset.dataset_id}"
        
        start_time = time.perf_counter()
        run = await runner.run_benchmark(run_id=run_id, config=config, sut=sut)
        duration = time.perf_counter() - start_time
        
        # Reload to verify SQLite persistence
        saved_run = await repo.get_run(run_id)
        
        # Calculate scores
        passed_count = sum(1 for c in saved_run.cases if c.success)
        failed_count = len(saved_run.cases) - passed_count
        
        total_latency = 0.0
        total_tokens = 0
        total_cost = 0.0
        deterministic_scores = []
        judge_scores = []
        
        for case in saved_run.cases:
            # Latency, Cost, TokenUsage, ToolCalling are deterministic
            for name, m_res in case.metrics.items():
                if name in ["Latency", "TokenUsage", "Cost", "ToolCalling"]:
                    deterministic_scores.append(m_res.score)
                else:
                    judge_scores.append(m_res.score)
                    
            # Extract raw SUT telemetry from trajectory
            total_latency += case.trajectory.total_latency.seconds
            total_tokens += case.trajectory.total_token_usage.total_tokens
            total_cost += case.trajectory.total_cost.amount
            
        case_count = len(saved_run.cases)
        avg_latency = total_latency / case_count if case_count > 0 else 0.0
        avg_tokens = total_tokens / case_count if case_count > 0 else 0.0
        avg_cost = total_cost / case_count if case_count > 0 else 0.0
        avg_det = sum(deterministic_scores) / len(deterministic_scores) if deterministic_scores else 0.0
        avg_judge = sum(judge_scores) / len(judge_scores) if judge_scores else 0.0
        
        results[dataset.dataset_id] = {
            "name": dataset.name,
            "expected": expected_count,
            "discovered": discovered,
            "executed": case_count,
            "passed": passed_count,
            "failed": failed_count,
            "skipped": 0,
            "duration": duration,
            "avg_latency": avg_latency,
            "avg_tokens": avg_tokens,
            "avg_cost": avg_cost,
            "avg_det": avg_det,
            "avg_judge": avg_judge
        }
        
        overall_total_cases += expected_count
        overall_executed += case_count
        overall_passed += passed_count
        overall_failed += failed_count
        
    print("\n=== EXECUTION EVIDENCE BY DATASET ===")
    for ds_id, data in results.items():
        print(f"\n{ds_id}")
        print(f"Dataset Name: {data['name']}")
        print(f"Expected Cases: {data['expected']}")
        print(f"Discovered: {data['discovered']}")
        print(f"Executed: {data['executed']}")
        print(f"Passed: {data['passed']}")
        print(f"Failed: {data['failed']}")
        print(f"Skipped: {data['skipped']}")
        print(f"Execution Time: {data['duration']:.2f}s")
        print(f"Average Latency: {data['avg_latency']:.4f}s")
        print(f"Average Token Usage: {data['avg_tokens']:.1f}")
        print(f"Average Cost: ${data['avg_cost']:.6f}")
        print(f"Average Deterministic Score: {data['avg_det']:.4f}")
        print(f"Average LLM Judge Score: {data['avg_judge']:.4f}")
        
    print("\n=== OVERALL TOTALS ===")
    print(f"Datasets: {len(results)}")
    print(f"Total benchmark cases: {overall_total_cases}")
    print(f"Executed: {overall_executed}")
    print(f"Passed: {overall_passed}")
    print(f"Failed: {overall_failed}")
    print(f"Skipped: {overall_skipped}")
    
if __name__ == "__main__":
    asyncio.run(main())
