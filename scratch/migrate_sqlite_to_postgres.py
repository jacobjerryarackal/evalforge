import os
import shutil
import sqlite3
import sys
import psycopg2


def migrate(sqlite_path: str, postgres_url: str):
    print("=== STARTING SQLITE TO POSTGRESQL DATA MIGRATION ===")

    if not os.path.exists(sqlite_path):
        print(f"ERROR: SQLite database file not found at {sqlite_path}")
        sys.exit(1)

    # 1. Back up SQLite database
    backup_path = sqlite_path + ".backup"
    print(f"Creating safety backup of {sqlite_path} at {backup_path}...")
    try:
        shutil.copyfile(sqlite_path, backup_path)
        print("Backup created successfully.")
    except Exception as e:
        print(f"ERROR creating backup: {e}")
        sys.exit(1)

    # 2. Connect to databases
    print("Connecting to SQLite source database...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    print("Connecting to PostgreSQL target database...")
    try:
        pg_conn = psycopg2.connect(postgres_url)
        pg_cur = pg_conn.cursor()
    except Exception as e:
        print(f"ERROR connecting to PostgreSQL: {e}")
        sqlite_conn.close()
        sys.exit(1)

    # Ensure PostgreSQL schemas exist first
    print("Ensuring PostgreSQL tables exist...")
    try:
        # Golden Datasets
        pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS golden_datasets (
                dataset_id TEXT,
                version TEXT,
                name TEXT,
                description TEXT,
                test_cases TEXT,
                metadata TEXT,
                PRIMARY KEY (dataset_id, version)
            )
        """)
        # Evaluation Runs
        pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_runs (
                run_id TEXT PRIMARY KEY,
                dataset_id TEXT,
                dataset_version TEXT,
                sut_version TEXT,
                timestamp TEXT,
                cases TEXT,
                parameters TEXT,
                summary TEXT,
                metadata TEXT
            )
        """)
        # Experiments
        pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                name TEXT,
                description TEXT,
                run_ids TEXT,
                metadata TEXT,
                created_at TEXT
            )
        """)
        pg_cur.execute("CREATE INDEX IF NOT EXISTS idx_datasets_id ON golden_datasets (dataset_id)")
        pg_cur.execute("CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs (dataset_id)")
        pg_conn.commit()
    except Exception as e:
        print(f"ERROR creating PostgreSQL schema: {e}")
        pg_conn.rollback()
        sqlite_conn.close()
        pg_conn.close()
        sys.exit(1)

    # 3. Migrate Golden Datasets
    print("\nMigrating table 'golden_datasets'...")
    try:
        sqlite_cur.execute(
            "SELECT dataset_id, version, name, description, test_cases, metadata FROM golden_datasets"
        )
        datasets = sqlite_cur.fetchall()
        print(f"Found {len(datasets)} dataset records in SQLite.")
        for ds in datasets:
            pg_cur.execute(
                """
                INSERT INTO golden_datasets (dataset_id, version, name, description, test_cases, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (dataset_id, version) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    test_cases = EXCLUDED.test_cases,
                    metadata = EXCLUDED.metadata
                """,
                (
                    ds["dataset_id"],
                    ds["version"],
                    ds["name"],
                    ds["description"],
                    ds["test_cases"],
                    ds["metadata"],
                ),
            )
        pg_conn.commit()
        print(f"Successfully migrated {len(datasets)} dataset records.")
    except Exception as e:
        print(f"ERROR migrating golden_datasets: {e}")
        pg_conn.rollback()

    # 4. Migrate Evaluation Runs
    print("\nMigrating table 'evaluation_runs'...")
    try:
        sqlite_cur.execute(
            """SELECT run_id, dataset_id, dataset_version, sut_version,
                      timestamp, cases, parameters, summary, metadata FROM evaluation_runs"""
        )
        runs = sqlite_cur.fetchall()
        print(f"Found {len(runs)} evaluation run records in SQLite.")
        for run in runs:
            pg_cur.execute(
                """
                INSERT INTO evaluation_runs
                (run_id, dataset_id, dataset_version, sut_version, timestamp,
                 cases, parameters, summary, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO UPDATE SET
                    dataset_id = EXCLUDED.dataset_id,
                    dataset_version = EXCLUDED.dataset_version,
                    sut_version = EXCLUDED.sut_version,
                    timestamp = EXCLUDED.timestamp,
                    cases = EXCLUDED.cases,
                    parameters = EXCLUDED.parameters,
                    summary = EXCLUDED.summary,
                    metadata = EXCLUDED.metadata
                """,
                (
                    run["run_id"],
                    run["dataset_id"],
                    run["dataset_version"],
                    run["sut_version"],
                    run["timestamp"],
                    run["cases"],
                    run["parameters"],
                    run["summary"],
                    run["metadata"],
                ),
            )
        pg_conn.commit()
        print(f"Successfully migrated {len(runs)} run records.")
    except Exception as e:
        print(f"ERROR migrating evaluation_runs: {e}")
        pg_conn.rollback()

    # 5. Migrate Experiments
    print("\nMigrating table 'experiments'...")
    try:
        sqlite_cur.execute(
            "SELECT experiment_id, name, description, run_ids, metadata, created_at FROM experiments"
        )
        experiments = sqlite_cur.fetchall()
        print(f"Found {len(experiments)} experiment records in SQLite.")
        for exp in experiments:
            pg_cur.execute(
                """
                INSERT INTO experiments
                (experiment_id, name, description, run_ids, metadata, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (experiment_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    run_ids = EXCLUDED.run_ids,
                    metadata = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
                """,
                (
                    exp["experiment_id"],
                    exp["name"],
                    exp["description"],
                    exp["run_ids"],
                    exp["metadata"],
                    exp["created_at"],
                ),
            )
        pg_conn.commit()
        print(f"Successfully migrated {len(experiments)} experiment records.")
    except Exception as e:
        print(f"ERROR migrating experiments: {e}")
        pg_conn.rollback()

    # 6. Verification and Assertions
    print("\n=== COMPARING DATABASE ROW COUNTS ===")
    has_mismatch = False

    # Dataset Counts
    sqlite_cur.execute("SELECT COUNT(*) FROM golden_datasets")
    sq_ds_count = sqlite_cur.fetchone()[0]
    pg_cur.execute("SELECT COUNT(*) FROM golden_datasets")
    pg_ds_count = pg_cur.fetchone()[0]
    ds_match = sq_ds_count == pg_ds_count
    print(
        f"golden_datasets: SQLite={sq_ds_count} | PostgreSQL={pg_ds_count} -> {'MATCH' if ds_match else 'MISMATCH'}"
    )
    if not ds_match:
        has_mismatch = True

    # Run Counts
    sqlite_cur.execute("SELECT COUNT(*) FROM evaluation_runs")
    sq_run_count = sqlite_cur.fetchone()[0]
    pg_cur.execute("SELECT COUNT(*) FROM evaluation_runs")
    pg_run_count = pg_cur.fetchone()[0]
    run_match = sq_run_count == pg_run_count
    print(
        f"evaluation_runs: SQLite={sq_run_count} | PostgreSQL={pg_run_count} -> {'MATCH' if run_match else 'MISMATCH'}"
    )
    if not run_match:
        has_mismatch = True

    # Experiment Counts
    sqlite_cur.execute("SELECT COUNT(*) FROM experiments")
    sq_exp_count = sqlite_cur.fetchone()[0]
    pg_cur.execute("SELECT COUNT(*) FROM experiments")
    pg_exp_count = pg_cur.fetchone()[0]
    exp_match = sq_exp_count == pg_exp_count
    print(
        f"experiments: SQLite={sq_exp_count} | PostgreSQL={pg_exp_count} -> {'MATCH' if exp_match else 'MISMATCH'}"
    )
    if not exp_match:
        has_mismatch = True

    # Clean up
    sqlite_conn.close()
    pg_conn.close()

    if has_mismatch:
        print("\nERROR: Database migration verified with discrepancies!")
        sys.exit(1)
    else:
        print("\nSUCCESS: Database migration completed successfully and verified!")


if __name__ == "__main__":
    sqlite_db = os.getenv("SQLITE_DB_PATH", "evalforge_platform.db")
    postgres_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/evalforge"
    )

    if len(sys.argv) > 1:
        sqlite_db = sys.argv[1]
    if len(sys.argv) > 2:
        postgres_url = sys.argv[2]

    migrate(sqlite_db, postgres_url)
