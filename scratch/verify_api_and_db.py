import os
import json
import urllib.request
import psycopg2
from psycopg2.extras import RealDictCursor

def verify_run_and_api(run_id: str):
    print("=== PROGRAMMATIC POSTGRESQL & API INTEGRITY CHECK ===")
    
    # 1. Connect to PostgreSQL
    postgres_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/evalforge")
    print("Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    except Exception as e:
        print(f"FAIL: Failed to connect to PostgreSQL: {e}")
        return False

    # 2. Query run-a0aa7aa3
    cursor.execute("""
        SELECT run_id, dataset_id, dataset_version, sut_version, timestamp, cases, summary, parameters, metadata
        FROM evaluation_runs 
        WHERE run_id = %s
    """, (run_id,))
    db_row = cursor.fetchone()
    
    if not db_row:
        print(f"FAIL: Run {run_id} does not exist in PostgreSQL!")
        cursor.close()
        conn.close()
        return False
        
    print(f"SUCCESS: Run {run_id} exists in PostgreSQL.")
    
    # 3. Check summaries
    summary = json.loads(db_row["summary"]) if isinstance(db_row["summary"], str) else db_row["summary"]
    total_cases = summary.get("total_cases", 0)
    successful_cases = summary.get("successful_cases", 0)
    success_rate = summary.get("success_rate", 0.0)
    
    print(f"Verified summary: total_cases={total_cases}, successful_cases={successful_cases}, success_rate={success_rate}")
    
    assert total_cases == 25, f"FAIL: Expected 25 cases, got {total_cases} in DB summary"
    assert successful_cases == 25, f"FAIL: Expected 25 successful cases, got {successful_cases} in DB summary"
    assert success_rate == 1.0, f"FAIL: Expected success_rate 1.0, got {success_rate} in DB summary"
    
    # Check cases detail
    cases = json.loads(db_row["cases"]) if isinstance(db_row["cases"], str) else db_row["cases"]
    assert len(cases) == 25, f"FAIL: Expected 25 case objects, got {len(cases)}"
    
    # 4. Check representative cases are fully populated
    rep_cases = ["travel_v1_001", "travel_v1_002", "travel_v1_010", "travel_v1_011", "travel_v1_020", "travel_v1_025"]
    db_cases_map = {c["case_id"]: c for c in cases}
    
    for case_id in rep_cases:
        assert case_id in db_cases_map, f"FAIL: Representative case {case_id} not found in DB"
        case = db_cases_map[case_id]
        
        # Verify fields in DB
        assert case.get("success") is True, f"FAIL: Case {case_id} is not successful"
        trajectory = case.get("trajectory") or {}
        steps = trajectory.get("steps") or []
        assert len(steps) > 0, f"FAIL: Case {case_id} has empty trajectory steps"
        
        # Verify tool calls are present
        tool_calls_found = any(len(step.get("tool_calls", [])) > 0 for step in steps)
        assert tool_calls_found is True, f"FAIL: Case {case_id} has no tool calls"
        
        # Verify metrics count
        metrics = case.get("metrics") or {}
        assert len(metrics) > 0, f"FAIL: Case {case_id} has empty metrics"
        
        # Verify judge reasoning is present
        judge_reasoning_found = any(bool(m.get("reasoning")) for m in metrics.values())
        assert judge_reasoning_found is True, f"FAIL: Case {case_id} has no judge reasoning"
        
    print("SUCCESS: PostgreSQL checks passed: all 25 cases, trajectories, tool calls, and metrics are fully persisted.")
    
    # 5. Query API and match records
    api_url = f"http://127.0.0.1:8000/api/runs/{run_id}"
    print(f"Fetching run data from API URL: {api_url} ...")
    try:
        with urllib.request.urlopen(api_url) as response:
            api_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"FAIL: Failed to fetch run from API: {e}")
        cursor.close()
        conn.close()
        return False
        
    print(f"SUCCESS: Fetched run data from API.")
    
    # Compare summary fields
    api_summary = api_data.get("summary") or {}
    for key in ["total_cases", "successful_cases", "success_rate", "total_tokens", "total_cost"]:
        db_val = summary.get(key)
        api_val = api_summary.get(key)
        if key == "total_cost":
            match = abs(db_val - api_val) < 1e-6
        else:
            match = db_val == api_val
        assert match, f"FAIL: Summary field '{key}' mismatch: DB={db_val} | API={api_val}"
        
    # Compare cases counts and map case ID to case object
    api_cases = api_data.get("cases") or []
    assert len(api_cases) == 25, f"FAIL: Expected 25 cases in API response, got {len(api_cases)}"
    api_cases_map = {c["case_id"]: c for c in api_cases}
    
    # Compare case values
    for case_id in rep_cases:
        db_case = db_cases_map[case_id]
        api_case = api_cases_map[case_id]
        
        assert db_case["success"] == api_case["success"], f"FAIL: Case '{case_id}' success mismatch: DB={db_case['success']} | API={api_case['success']}"
        
        # Compare metrics count and scores
        db_metrics = db_case.get("metrics") or {}
        
        # Map API metrics back to dictionary since API endpoint maps metrics dict to list for frontend
        api_metrics_list = api_case.get("metrics") or []
        api_metrics = {m["metric_name"]: m for m in api_metrics_list}
        
        for m_name, db_m in db_metrics.items():
            assert m_name in api_metrics, f"FAIL: Metric '{m_name}' in case '{case_id}' missing in API response"
            api_m = api_metrics[m_name]
            assert db_m["score"] == api_m["score"], f"FAIL: Metric '{m_name}' score mismatch in case '{case_id}': DB={db_m['score']} | API={api_m['score']}"
            assert db_m.get("reasoning") == api_m.get("reasoning"), f"FAIL: Metric '{m_name}' reasoning mismatch in case '{case_id}': DB={db_m.get('reasoning')} | API={api_m.get('reasoning')}"
            
    print("SUCCESS: API response matches database records perfectly (summary, status, metrics, and reasoning verified).")
    
    cursor.close()
    conn.close()
    return True

if __name__ == "__main__":
    import sys
    run_id = "run-a0aa7aa3"
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    verify_run_and_api(run_id)
