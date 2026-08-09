# EvalForge SQLite to PostgreSQL Migration Plan

This document details the design and deployment plan for migrating the persistence layer from SQLite to PostgreSQL.

---

## 1. Database Architecture

We will preserve the simple document-based design currently used in SQLite. The database schema in PostgreSQL will match SQLite's structure column-for-column to avoid changes to downstream serialization/deserialization logic.

### Tables DDL (PostgreSQL)

```sql
CREATE TABLE IF NOT EXISTS golden_datasets (
    dataset_id TEXT,
    version TEXT,
    name TEXT,
    description TEXT,
    test_cases TEXT, -- JSON document
    metadata TEXT,   -- JSON document
    PRIMARY KEY (dataset_id, version)
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    run_id TEXT PRIMARY KEY,
    dataset_id TEXT,
    dataset_version TEXT,
    sut_version TEXT,
    timestamp TEXT,  -- ISO-8601 string representation
    cases TEXT,      -- JSON document
    parameters TEXT, -- JSON document
    summary TEXT,    -- JSON document
    metadata TEXT    -- JSON document
);

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    run_ids TEXT,     -- JSON document (list of run_ids)
    metadata TEXT,    -- JSON document
    created_at TEXT   -- ISO-8601 string representation
);

CREATE INDEX IF NOT EXISTS idx_datasets_id ON golden_datasets (dataset_id);
CREATE INDEX IF NOT EXISTS idx_runs_dataset ON evaluation_runs (dataset_id);
```

---

## 2. Connection Management & Pooling

To ensure thread-safety when running under `asyncio.to_thread()`, we will use a thread-safe connection pool from `psycopg2.pool`:

*   **Pool Class**: `psycopg2.pool.ThreadedConnectionPool`
*   **Minimum Connections**: `2` (handles startup checks and baseline concurrent requests)
*   **Maximum Connections**: `20` (bounded to match FastAPI/uvicorn default worker configurations)
*   **Context Manager**: A custom connection context helper that acquires and releases connections safely back to the pool, even on errors:

```python
from contextlib import contextmanager

@contextmanager
def get_connection(self):
    conn = self.pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        self.pool.putconn(conn)
```

---

## 3. Environment Variables

*   `DATABASE_URL`: Connection string for PostgreSQL database.
    *   Example: `postgresql://postgres:postgres@localhost:5432/evalforge`
    *   If `DATABASE_URL` is not present, is empty, or does not start with `postgresql://` or `postgres://`, the application will fall back to local SQLite persistence to maintain compatibility.

---

## 4. Local Development Strategy

To allow developers to run PostgreSQL locally without installing it on the host OS:
1.  Extend the workspace's [docker-compose.yml](file:///d:/AI/evalforge/docker-compose.yml) to spin up a PostgreSQL service.
2.  Pre-configure a default user (`postgres`), password (`postgres`), and database name (`evalforge`).
3.  Add instructions in `README.md` on starting the service (`docker-compose up -d db`).

---

## 5. Test Database Strategy

1.  **Unit Tests**: By default, the unit test suite (`pytest`) will run against local/in-memory database states. SQLite (`temp_db` fixture) will be used for testing `SqliteEvaluationRepository`.
2.  **Integration Tests**: We will create `tests/integration/test_postgres_repository.py` to verify PostgreSQL CRUD operations. This test will:
    *   Check for a `TEST_DATABASE_URL` or `DATABASE_URL` environment variable.
    *   If available, execute all tests against PostgreSQL (in a isolated database or clean tables).
    *   If not available, skip the PostgreSQL tests with a warning, keeping the standard test run dependency-free.

---

## 6. Schema Migration Strategy

*   The `PostgresEvaluationRepository` will run table initialization on startup (via `_init_db()` in constructor) using `CREATE TABLE IF NOT EXISTS` commands.
*   This approach avoids the complexity of Alembic/Alembic migrations, matching the existing SQLite startup initialization and keeping deployments zero-config.

---

## 7. Data Migration Strategy

To transfer verified data (such as the certified `travel_v1` run history) from the local SQLite database (`evalforge_platform.db`) to the production PostgreSQL database:
1.  We will provide a migration CLI script: `scratch/migrate_sqlite_to_postgres.py`.
2.  The script will:
    *   Accept local SQLite path and PostgreSQL URL via command-line arguments or environment variables.
    *   Create a file-level backup of the SQLite database before execution.
    *   Read records from SQLite tables (`golden_datasets`, `evaluation_runs`, `experiments`).
    *   Insert records into PostgreSQL using appropriate `ON CONFLICT` (UPSERT) commands.
    *   Compare table row counts between the source and target databases.
    *   Verify representative values to guarantee no data truncation or encoding corruption occurred.

---

## 8. Rollback Strategy

Because PostgreSQL and SQLite share identical schemas:
1.  **Backwards Compatibility**: The application can be rolled back to SQLite at any time by unsetting or updating the `DATABASE_URL` env variable.
2.  **Data Reverse Sync**: If production data is written to PostgreSQL and needs to be pulled back to a local SQLite database, the migration script can be run in reverse mode (copying from Postgres to SQLite).

---

## 9. Production Deployment Strategy (Render/Vercel)

*   **Backend (Render)**:
    *   Add `DATABASE_URL` environment variable pointing to Render's managed PostgreSQL instance.
    *   Ensure the startup command runs database schema initialization on boot.
    *   Validate CORS to allow access from the Vercel frontend URL.
*   **Frontend (Vercel)**:
    *   Configure `NEXT_PUBLIC_API_URL` pointing to the Render backend URL.
