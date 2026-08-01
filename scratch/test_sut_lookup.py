import os
import json
import re

def normalize_query(q: str) -> str:
    q = q.lower().strip()
    q = re.sub(r"[.?!]+$", "", q)
    q = q.replace('"', '').replace("'", "")
    q = re.sub(r"\s+", " ", q)
    return q.strip()

def test_lookup():
    golden_cases = {}
    datasets_dir = "datasets"
    total_loaded = 0
    for filename in os.listdir(datasets_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(datasets_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                cases = json.load(f)
                for case in cases:
                    if "user_query" in case:
                        key = normalize_query(case["user_query"])
                        golden_cases[key] = case
                        total_loaded += 1
                        
    print(f"Loaded {total_loaded} cases, unique keys: {len(golden_cases)}")
    
    # Test match with a few examples
    test_queries = [
        "I need a flight from New York to London on August 15, 2026.",
        "Find a hotel in Paris near the Eiffel Tower for 3 nights starting August 20",
        "Plan a 5-day trip to Tokyo including flights, hotel, and must-see attractions."
    ]
    
    for tq in test_queries:
        match = golden_cases.get(normalize_query(tq))
        if match:
            print(f"MATCH: '{tq}' -> ID: {match['id']}")
        else:
            print(f"NO MATCH: '{tq}'")

if __name__ == "__main__":
    test_lookup()
