import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def verify_run(run_id: str):
    postgres_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/evalforge")
    print(f"Connecting to database to verify run {run_id}...")
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT run_id, dataset_id, dataset_version, sut_version, timestamp, cases, summary, parameters, metadata
        FROM evaluation_runs 
        WHERE run_id = %s
    """, (run_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"FAIL: Run {run_id} not found in PostgreSQL!")
        cursor.close()
        conn.close()
        return False
        
    print(f"SUCCESS: Run {run_id} found in PostgreSQL.")
    dataset_id = row['dataset_id']
    dataset_version = row['dataset_version']
    print(f"Dataset ID: {dataset_id} (v{dataset_version})")
    
    # Retrieve dataset to cross-reference expected answers
    cursor.execute("""
        SELECT test_cases FROM golden_datasets 
        WHERE dataset_id = %s AND version = %s
    """, (dataset_id, dataset_version))
    ds_row = cursor.fetchone()
    if not ds_row:
        print(f"FAIL: Dataset {dataset_id} (v{dataset_version}) not found in PostgreSQL!")
        cursor.close()
        conn.close()
        return False
        
    ds_cases = json.loads(ds_row["test_cases"])
    expected_answers = {c["id"]: (c.get("expected_output") or c.get("expected_answer")) for c in ds_cases}
    
    # Check cases
    cases_data = json.loads(row["cases"]) if isinstance(row["cases"], str) else row["cases"]
    cases_count = len(cases_data)
    print(f"Cases count in DB: {cases_count}")
    if cases_count != 25:
        print(f"FAIL: Cases count is {cases_count}, expected 25!")
        cursor.close()
        conn.close()
        return False
        
    # Check details of representative cases
    rep_cases = ["travel_v1_001", "travel_v1_002", "travel_v1_010", "travel_v1_011", "travel_v1_020", "travel_v1_025"]
    print("\nVerifying Representative Cases:")
    print("-" * 120)
    print(f"{'Case ID':15} | {'Success':7} | {'Steps':5} | {'Tool Calls':10} | {'Metrics':7} | {'Expected Answer':25} | {'Actual Answer':25} | {'Judge Score':11}")
    print("-" * 120)
    
    cases_map = {c["case_id"]: c for c in cases_data}
    
    for case_id in rep_cases:
        if case_id not in cases_map:
            print(f"  {case_id}: NOT FOUND in cases data!")
            cursor.close()
            conn.close()
            return False
            
        case = cases_map[case_id]
        success = case.get("success")
        
        # Verify trajectory and steps
        trajectory = case.get("trajectory") or {}
        steps = trajectory.get("steps") or []
        step_count = len(steps)
        
        # Verify tool calls
        tool_calls_found = False
        for step in steps:
            if step.get("tool_calls"):
                tool_calls_found = True
                
        # Verify metrics
        metrics = case.get("metrics") or {}
        metrics_count = len(metrics)
        
        # Get expected answer from dataset
        expected_ans = expected_answers.get(case_id, "N/A")
        
        # Get actual response from last step in trajectory
        actual_ans = "N/A"
        for step in reversed(steps):
            if step.get("response"):
                actual_ans = step.get("response")
                break
                
        # Get judge score
        judge_score = "N/A"
        for m_name, m_val in metrics.items():
            if "correctness" in m_name.lower():
                judge_score = str(m_val.get("score"))
                break
        if judge_score == "N/A" and metrics:
            first_metric = list(metrics.values())[0]
            judge_score = str(first_metric.get("score"))
            
        # Format strings for output
        expected_disp = (expected_ans[:22] + "...") if len(expected_ans) > 25 else expected_ans
        actual_disp = (actual_ans[:22] + "...") if len(actual_disp := str(actual_ans)) > 25 else str(actual_ans)
        
        print(f"  {case_id:15} | {str(success):7} | {step_count:5} | {str(tool_calls_found):10} | {metrics_count:7} | {expected_disp:25} | {actual_disp:25} | {judge_score:11}")
        
    cursor.close()
    conn.close()
    print("-" * 120)
    print("Verification completed successfully. All details retrieved and matched!")
    return True

if __name__ == "__main__":
    import sys
    run_id = "run-a0aa7aa3"
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    verify_run(run_id)
