import sqlite3
import json
import urllib.request

def main():
    print("=== Cross-Layer Audit: SQLite vs API ===")
    
    # 1. Load from Database (Postgres or SQLite fallback)
    import os
    database_url = os.getenv("DATABASE_URL")
    if database_url and (database_url.startswith("postgresql://") or database_url.startswith("postgres://")):
        print("Connecting to PostgreSQL database for audit...")
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT cases, summary FROM evaluation_runs WHERE run_id = 'run-platform-travel-v1'")
        db_row = cursor.fetchone()
        if not db_row:
            print("ERROR: Run 'run-platform-travel-v1' not found in PostgreSQL.")
            conn.close()
            return
    else:
        print("Connecting to SQLite database for audit...")
        conn = sqlite3.connect("evalforge_platform.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT cases, summary FROM evaluation_runs WHERE run_id = 'run-platform-travel-v1'")
        db_row = cursor.fetchone()
        if not db_row:
            print("ERROR: Run 'run-platform-travel-v1' not found in SQLite.")
            conn.close()
            return
        
    db_cases = json.loads(db_row["cases"])
    db_summary = json.loads(db_row["summary"])
    
    # Map DB cases by case_id for lookup
    db_cases_map = {c["case_id"]: c for c in db_cases}
    
    # 2. Load from API
    try:
        with urllib.request.urlopen("http://localhost:8000/api/runs/run-platform-travel-v1") as response:
            api_data = json.loads(response.read().decode())
    except Exception as e:
        print(f"ERROR fetching from API: {e}")
        return
        
    api_cases = api_data.get("cases", [])
    api_summary = api_data.get("summary", {})
    
    # Map API cases by case_id
    api_cases_map = {c["case_id"]: c for c in api_cases}
    
    # 3. Compare summaries
    print("\nAuditing Run Summary:")
    summary_fields = ["total_cases", "successful_cases", "success_rate", "total_tokens", "total_cost"]
    for f in summary_fields:
        db_val = db_summary.get(f)
        api_val = api_summary.get(f)
        # Handle small rounding differences in cost
        if f == "total_cost":
            match = abs(db_val - api_val) < 1e-6
        else:
            match = db_val == api_val
        print(f"  {f:18}: DB={db_val} | API={api_val} -> {'MATCH' if match else 'MISMATCH'}")
        if not match:
            print("  WARNING: Summary mismatch found!")

    # 4. Compare Case-by-Case
    print(f"\nAuditing {len(db_cases_map)} Cases:")
    mismatch_count = 0
    
    for case_id in sorted(db_cases_map.keys()):
        if case_id not in api_cases_map:
            print(f"  [{case_id}] ERROR: Missing in API response.")
            mismatch_count += 1
            continue
            
        db_case = db_cases_map[case_id]
        api_case = api_cases_map[case_id]
        
        # Check overall success
        success_match = db_case["success"] == api_case["success"]
        
        # Check metrics
        db_metrics = db_case.get("metrics", {})
        api_metrics = {m["metric_name"]: m for m in api_case.get("metrics", [])}
        
        metrics_match = True
        metrics_details = []
        for m_name, db_m in db_metrics.items():
            if m_name not in api_metrics:
                metrics_match = False
                metrics_details.append(f"Metric '{m_name}' missing in API")
                continue
                
            api_m = api_metrics[m_name]
            score_match = db_m["score"] == api_m["score"]
            reason_match = db_m.get("reasoning") == api_m.get("reasoning")
            
            if not (score_match and reason_match):
                metrics_match = False
                metrics_details.append(
                    f"Metric '{m_name}' mismatch: "
                    f"DB(score={db_m['score']}, reason={db_m.get('reasoning')}) vs "
                    f"API(score={api_m['score']}, reason={api_m.get('reasoning')})"
                )
        
        # Check trajectory response / expected tool calls
        db_traj = db_case.get("trajectory", {})
        api_traj = api_case.get("trajectory", {})
        db_steps = db_traj.get("steps", [])
        api_steps = api_traj.get("steps", [])
        
        steps_match = len(db_steps) == len(api_steps)
        if steps_match:
            for idx in range(len(db_steps)):
                db_tcs = db_steps[idx].get("tool_calls", [])
                api_tcs = api_steps[idx].get("tool_calls", [])
                if len(db_tcs) != len(api_tcs):
                    steps_match = False
                    break
                for tc_idx in range(len(db_tcs)):
                    if db_tcs[tc_idx]["tool_name"] != api_tcs[tc_idx]["tool_name"]:
                        steps_match = False
                        break
        
        case_match = success_match and metrics_match and steps_match
        
        if case_match:
            print(f"  [{case_id}] [OK] DB matches API perfectly. Success={db_case['success']}. Metrics Count={len(db_metrics)}")
        else:
            print(f"  [{case_id}] [MISMATCH] MISMATCH FOUND!")
            print(f"    Success Match: {success_match} (DB={db_case['success']}, API={api_case['success']})")
            print(f"    Steps Match: {steps_match}")
            if not metrics_match:
                print(f"    Metrics Mismatch Details:")
                for d in metrics_details:
                    print(f"      - {d}")
            mismatch_count += 1
            
    print(f"\nAudit complete. Total Mismatches: {mismatch_count}")

if __name__ == "__main__":
    main()
