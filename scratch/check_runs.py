import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def main():
    postgres_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345678@localhost:5432/evalforge")
    print(f"Connecting to database...")
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT run_id, dataset_id, dataset_version, sut_version, timestamp, summary 
        FROM evaluation_runs 
        ORDER BY timestamp DESC
    """)
    rows = cursor.fetchall()
    
    print(f"\nFound {len(rows)} runs in PostgreSQL:\n")
    print(f"{'Run ID':30} | {'Dataset':20} | {'Version':8} | {'Success Rate':12} | {'Timestamp'}")
    print("-" * 90)
    for r in rows:
        summary = json.loads(r["summary"]) if isinstance(r["summary"], str) else r["summary"]
        success_rate = f"{summary.get('success_rate', 0.0) * 100:.1f}%" if summary else "N/A"
        print(f"{r['run_id']:30} | {r['dataset_id']:20} | {r['dataset_version']:8} | {success_rate:12} | {r['timestamp']}")
        
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
