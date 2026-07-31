import asyncio
from src.adapters.repositories.sqlite_repository import SqliteEvaluationRepository

async def main():
    repo = SqliteEvaluationRepository("evalforge_platform.db")
    runs = await repo.list_runs()
    print(f"Total runs: {len(runs)}")
    for r in runs:
        print(f"Run ID: {r.run_id}")
        print(f"  Dataset ID: {r.dataset_id} (v{r.dataset_version})")
        print(f"  Summary: {r.summary}")
        
        # Load run details to see individual cases
        run_detail = await repo.get_run(r.run_id)
        if run_detail and run_detail.cases:
            print("  First case evaluation example:")
            c = run_detail.cases[0]
            print(f"    Case ID: {c.case_id}")
            print(f"    Success: {c.success}")
            print(f"    Metrics:")
            for m_name, m_res in c.metrics.items():
                print(f"      {m_name}: score={m_res.score}, reasoning={m_res.reasoning}")
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(main())
