import os
import json

def audit_datasets():
    datasets_dir = "datasets"
    expected_counts = {
        "travel_v1.json": 25,
        "travel_tool_calls.json": 20,
        "travel_long_context.json": 20,
        "travel_regression.json": 15,
        "travel_missing_context.json": 15,
        "travel_edge_cases.json": 20,
        "travel_safety.json": 20,
        "travel_adversarial.json": 15,
        "travel_multilingual.json": 15,
        "travel_provider_benchmark.json": 15
    }
    
    files = sorted(os.listdir(datasets_dir))
    all_case_ids = set()
    duplicate_ids = []
    issues = []
    
    print("=== EvalForge Dataset Integrity Audit ===")
    for filename in files:
        if not filename.endswith(".json"):
            continue
            
        path = os.path.join(datasets_dir, filename)
        print(f"\nAuditing: {filename}")
        
        # 1. JSON Validity
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            issues.append(f"{filename}: Invalid JSON format - {e}")
            print(f"  [FAIL] JSON Parsing Error: {e}")
            continue
            
        # 2. Check structure
        if not isinstance(data, list):
            issues.append(f"{filename}: Root is not a JSON list")
            print("  [FAIL] Root is not a list")
            continue
            
        case_count = len(data)
        expected = expected_counts.get(filename, 0)
        status = "PASS" if case_count == expected else "FAIL"
        print(f"  Cases Count: {case_count} (Expected: {expected}) -> {status}")
        if case_count != expected:
            issues.append(f"{filename}: Case count mismatch (got {case_count}, expected {expected})")
            
        # 3. Audit individual cases
        for idx, case in enumerate(data):
            case_id = case.get("id") or case.get("case_id")
            if not case_id:
                issues.append(f"{filename}[index {idx}]: Missing ID")
                continue
                
            if case_id in all_case_ids:
                duplicate_ids.append(case_id)
                issues.append(f"{filename}: Duplicate ID found: '{case_id}'")
            all_case_ids.add(case_id)
            
            # Check mandatory fields
            query = case.get("user_query") or case.get("input_query")
            if not query:
                issues.append(f"{filename}[{case_id}]: Missing query field")
                
            expected_ans = case.get("expected_answer") or case.get("expected_output")
            if not expected_ans:
                issues.append(f"{filename}[{case_id}]: Missing expected answer")
                
            # Check constraints structure
            for constraint in ["latency_constraint", "token_constraint", "cost_constraint"]:
                if constraint in case:
                    val = case[constraint]
                    if not isinstance(val, (int, float)) or val < 0:
                        issues.append(f"{filename}[{case_id}]: Invalid constraint value for {constraint} = {val}")
                        
            # Check expected_metrics / expected_judge_scores
            if "expected_metrics" in case:
                metrics = case["expected_metrics"]
                if not isinstance(metrics, dict):
                    issues.append(f"{filename}[{case_id}]: expected_metrics is not a JSON object")
            if "expected_judge_scores" in case:
                scores = case["expected_judge_scores"]
                if not isinstance(scores, dict):
                    issues.append(f"{filename}[{case_id}]: expected_judge_scores is not a JSON object")
                    
    print("\n=== Audit Summary ===")
    print(f"Total Unique Case IDs collected: {len(all_case_ids)}")
    print(f"Total duplicate IDs found: {len(duplicate_ids)}")
    if duplicate_ids:
        print(f"Duplicate IDs: {duplicate_ids}")
    print(f"Total integrity issues found: {len(issues)}")
    for issue in issues:
        print(f"  - {issue}")
        
if __name__ == "__main__":
    audit_datasets()
