import asyncio
import json
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository

async def inspect():
    repo = SqliteEvaluationRepository("evalforge_platform.db")
    for run_id in ["run-f80f617a", "run-1303d5b5"]:
        print(f"=== Inspecting Run ID: {run_id} ===")
        run = await repo.get_run(run_id)
        if not run:
            print(f"Run {run_id} not found.")
            continue
        print(f"Dataset ID: {run.dataset_id} (v{run.dataset_version})")
        print(f"SUT Version: {run.sut_version}")
        print(f"Timestamp: {run.timestamp}")
        print(f"Summary: {run.summary}")
        
        # Get case travel_v1_001
        case_eval = next((c for c in run.cases if c.case_id == "travel_v1_001"), None)
        if not case_eval:
            print("travel_v1_001 not found in this run.")
            continue
            
        print(f"Success: {case_eval.success}")
        print("Trajectory Steps:")
        for step in case_eval.trajectory.steps:
            print(f"  Step {step.step_number}:")
            print(f"    Thought: {step.thought}")
            print(f"    Tool Calls: {step.tool_calls}")
            print(f"    Observation: {step.observation}")
            print(f"    Response: {step.response}")
            print(f"    Token Usage: {step.token_usage}")
            print(f"    Cost: {step.cost}")
            print(f"    Latency: {step.latency}")
            print(f"    Metadata: {step.metadata}")
            
        print("Metrics Results:")
        for m_name, m_res in case_eval.metrics.items():
            print(f"  Metric: {m_name}")
            print(f"    Score: {m_res.score}")
            print(f"    Reasoning: {m_res.reasoning}")
            print(f"    Metadata: {m_res.metadata}")
        print("-" * 80)

if __name__ == "__main__":
    asyncio.run(inspect())
