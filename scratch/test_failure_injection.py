import asyncio
import json
import os
from src.use_cases.datasets.loader import DatasetLoader
from src.adapters.llm.gemini import GeminiProvider
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository
from src.use_cases.metrics.registry import create_default_registry
from src.use_cases.runners.benchmark_runner import BenchmarkRunner
from src.domain.entities.benchmark_config import BenchmarkConfig, RetryPolicy
from src.domain.entities.dataset import GoldenDataset, GoldenTestCase
from examples.travel_agent.travel_agent_sut import TravelAgentSUT

async def main():
    print("=== EvalForge Failure Injection Tests ===")
    loader = DatasetLoader()
    
    # Test 1: Malformed JSON file loading
    print("\nTest 1: Loading malformed JSON file...")
    malformed_path = "scratch/malformed.json"
    with open(malformed_path, "w") as f:
        f.write("[ { 'id': 'invalid_json', ") # Unclosed brackets and single quotes
        
    try:
        loader.load_json(malformed_path)
        print("  [FAIL] Did not catch malformed JSON exception")
    except json.JSONDecodeError as e:
        print(f"  [PASS] Caught JSONDecodeError gracefully: {e}")
    except Exception as e:
        print(f"  [PASS] Caught exception: {e}")
        
    if os.path.exists(malformed_path):
        os.remove(malformed_path)

    # Test 2: Gemini Provider with missing / invalid model name
    print("\nTest 2: Gemini Provider with invalid model name...")
    try:
        provider = GeminiProvider(mock_mode=False, model_name="models/invalid-model-name")
        res = await provider.generate_text("Hi")
        print("  [FAIL] Invalid model succeeded somehow?")
    except Exception as e:
        print(f"  [PASS] Caught invalid model exception: {e}")

    # Test 3: Benchmark run with missing expected answer in GoldenTestCase
    print("\nTest 3: Case execution with missing expected_answer...")
    case = GoldenTestCase(
        id="tc-missing-ans",
        user_query="Hello",
        expected_answer="" # Missing expected answer
    )
    dataset = GoldenDataset(
        dataset_id="ds-missing-ans",
        name="Missing Ans",
        version="1.0.0",
        test_cases=[case]
    )
    sut = TravelAgentSUT()
    mock_provider = GeminiProvider(mock_mode=True)
    registry = create_default_registry(mock_provider)
    repo = SqliteEvaluationRepository("evalforge_platform_failure_test.db")
    runner = BenchmarkRunner(repository=repo, registry=registry)
    
    evaluators = list(registry.list_evaluators())
    config = BenchmarkConfig(
        dataset=dataset,
        provider="Gemini (Mock)",
        evaluators=evaluators,
        concurrency=1,
        retry_policy=RetryPolicy(max_retries=1)
    )
    
    try:
        run = await runner.run_benchmark(run_id="run-failure-test-1", config=config, sut=sut)
        print(f"  [PASS] Benchmark execution handled missing expected answer. Run ID: {run.run_id}")
    except Exception as e:
        print(f"  [FAIL] Benchmark runner crashed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
