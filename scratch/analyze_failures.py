import asyncio
import os
from collections import defaultdict
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.adapters.llm.gemini import GeminiProvider
from src.use_cases.runners.benchmark_runner import BenchmarkRunner, _get_case_threshold
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

DATASETS = [
    "travel_v1.json",
    "travel_tool_calls.json",
    "travel_long_context.json",
    "travel_regression.json",
    "travel_safety.json",
    "travel_missing_context.json",
    "travel_edge_cases.json",
    "travel_multilingual.json",
    "travel_adversarial.json",
    "travel_provider_benchmark.json"
]

async def main():
    loader = DatasetLoader()
    provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(provider)
    repo = SqliteEvaluationRepository("evalforge_failure_analysis.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    evaluators = list(registry.list_evaluators())
    sut = TravelAgentSUT()
    
    failure_details = []
    failure_by_metric = defaultdict(int)
    total_cases_run = 0
    
    for filename in DATASETS:
        path = os.path.join("datasets", filename)
        dataset = loader.load_json(path)
        
        config = BenchmarkConfig(
            dataset=dataset,
            provider="Gemini (Mock)",
            evaluators=evaluators,
            concurrency=5,
            retry_policy=RetryPolicy(max_retries=1)
        )
        
        run_id = f"run-analysis-{dataset.dataset_id}"
        run = await runner.run_benchmark(run_id=run_id, config=config, sut=sut)
        
        for case_eval in run.cases:
            total_cases_run += 1
            if not case_eval.success:
                failed_metrics = []
                for name, m_res in case_eval.metrics.items():
                    score = m_res.score
                    # Load expected threshold
                    case_def = dataset.get_case(case_eval.case_id)
                    threshold = _get_case_threshold(case_def, name)
                    
                    if threshold is None and name in ["Latency", "TokenUsage", "Cost", "ToolCalling"]:
                        threshold = 0.5
                    
                    if threshold is not None:
                        is_failed = False
                        if name.lower() == "hallucination":
                            if score > threshold:
                                is_failed = True
                        else:
                            if score < threshold:
                                is_failed = True
                                
                        if is_failed:
                            failed_metrics.append({
                                "metric": name,
                                "actual": score,
                                "expected": threshold,
                                "reasoning": m_res.reasoning
                            })
                            failure_by_metric[name] += 1
                            
                failure_details.append({
                    "dataset": dataset.dataset_id,
                    "case_id": case_eval.case_id,
                    "failed_metrics": failed_metrics
                })
                
    # Save the output reports
    with open("scratch/failure_analysis_output.txt", "w", encoding="utf-8") as f_out:
        f_out.write("=== ANALYSIS OF CRITICAL FAILURES ===\n")
        f_out.write(f"Total Cases Checked: {total_cases_run}\n")
        f_out.write(f"Total Failed Cases: {len(failure_details)}\n")
        
        f_out.write("\n--- Failure Counts & Percentages by Metric ---\n")
        for metric, count in sorted(failure_by_metric.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total_cases_run) * 100
            f_out.write(f"{metric}: {count} cases ({pct:.1f}%)\n")
            
        f_out.write("\n--- Raw Programmatic Failure Log ---\n")
        for case in failure_details:
            f_out.write(f"\nDataset: {case['dataset']} | Case ID: {case['case_id']}\n")
            for f in case["failed_metrics"]:
                f_out.write(f"  Metric: {f['metric']} | Actual: {f['actual']} | Expected: {f['expected']}\n")
                f_out.write(f"  Reason: {f['reasoning']}\n")

if __name__ == "__main__":
    asyncio.run(main())
