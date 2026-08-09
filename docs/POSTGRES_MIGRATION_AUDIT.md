# EvalForge SQLite to PostgreSQL Migration Audit

This document presents the detailed audit of the current EvalForge persistence layer, identifying all database structures, data access locations, and migration considerations.

---

## 1. Current Database Architecture

EvalForge uses an **Abstract Repository Pattern** to decouple the domain layer from concrete data storage. The repository interface is defined in:
*   [repository.py](file:///d:/AI/evalforge/src/domain/interfaces/repository.py): Defines the `EvaluationRepository` abstract base class (ABC) with methods for saving and retrieving Golden Datasets, Evaluation Runs, and Experiments.

The current production implementation uses SQLite:
*   [sqlite_repository.py](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py): Concrete implementation `SqliteEvaluationRepository` using Python's standard `sqlite3` library.
*   **Concurrency Model**: Because `sqlite3` calls are blocking, the repository uses `asyncio.to_thread()` to execute all database operations (inserts, updates, queries) in a thread pool, preventing event loop blocking.

---

## 2. Current SQLite Tables, Columns, and Data Types

SQLite uses three tables configured with minimal relational constraints, storing complex nested structures as JSON documents inside `TEXT` columns:

### 2.1 Table: `golden_datasets`
Stores benchmark datasets and versions.
*   `dataset_id` (TEXT)
*   `version` (TEXT)
*   `name` (TEXT)
*   `description` (TEXT)
*   `test_cases` (TEXT): JSON-serialized list of `GoldenTestCase` objects.
*   `metadata` (TEXT): JSON-serialized dictionary of metadata.
*   **Primary Key**: `(dataset_id, version)`
*   **Index**: `idx_datasets_id` on `(dataset_id)`

### 2.2 Table: `evaluation_runs`
Stores execution history, trajectories, metrics, and judge reasoning.
*   `run_id` (TEXT): Primary Key.
*   `dataset_id` (TEXT)
*   `dataset_version` (TEXT)
*   `sut_version` (TEXT)
*   `timestamp` (TEXT): ISO-8601 string representation of the execution datetime.
*   `cases` (TEXT): JSON-serialized list of `TestCaseEvaluation` objects (which includes the full SUT trajectory steps, expected tool calls, actual tool calls, metrics, and judge scores/reasoning).
*   `parameters` (TEXT): JSON-serialized execution parameters.
*   `summary` (TEXT): JSON-serialized summary metrics.
*   `metadata` (TEXT): JSON-serialized metadata.
*   **Primary Key**: `run_id`
*   **Index**: `idx_runs_dataset` on `(dataset_id)`

### 2.3 Table: `experiments`
Stores groups of runs comparing SUT behaviors.
*   `experiment_id` (TEXT): Primary Key.
*   `name` (TEXT)
*   `description` (TEXT)
*   `run_ids` (TEXT): JSON-serialized list of run ID strings (`["run_1", "run_2"]`).
*   `metadata` (TEXT): JSON-serialized metadata.
*   `created_at` (TEXT): ISO-8601 string representation of the creation datetime.
*   **Primary Key**: `experiment_id`

---

## 3. Relationships

The database is structurally denormalized. Relationships are maintained implicitly at the application layer:
1.  **Run-to-Dataset**: `evaluation_runs.dataset_id` and `evaluation_runs.dataset_version` map to `golden_datasets(dataset_id, version)`.
2.  **Experiment-to-Runs**: `experiments.run_ids` stores a serialized list of `run_id` strings matching `evaluation_runs.run_id`.
    *   When loading an `Experiment`, `SqliteEvaluationRepository.get_experiment()` loads the list of run IDs and performs sequential `get_run(run_id)` calls to build the `Experiment` domain entity with complete nested run histories.

---

## 4. SQLite-Specific Code Locations

### 4.1 SQL Statements and DDL
All database setup and SQL statements are defined within:
*   [sqlite_repository.py](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py):
    *   **Table Creation**: In `_init_db()` (lines 30–74).
    *   **Placeholders**: Uses `?` (lines 89, 118, 128, 204, 234, 285, 344, 371).
    *   **Upsert Syntax**: Uses `INSERT OR REPLACE INTO` (lines 89, 204, 344).
    *   **Sorting/Limits**: Uses `ORDER BY version DESC LIMIT 1` (line 131).

### 4.2 Application and Service Code
*   [app.py](file:///d:/AI/evalforge/src/adapters/api/app.py):
    *   Line 12: Imports `SqliteEvaluationRepository`.
    *   Line 48-49: Initializes database file path `db_path = "evalforge_platform.db"` and instantiates `repo = SqliteEvaluationRepository(db_path=db_path)`.
*   [audit_runs_trace.py](file:///d:/AI/evalforge/scratch/audit_runs_trace.py):
    *   Line 1: Imports `sqlite3`.
    *   Line 9-10: Connects directly to `evalforge_platform.db` using sqlite3 library for custom validation.

### 4.3 Scripts and Scratch Utilities
Several utility scripts instantiate their own SQLite repositories with custom DB files:
*   `scratch/run_full_certification.py` -> `evalforge_certification_evidence.db`
*   `scratch/run_real_validation.py` -> `evalforge_real_validation.db`
*   `scratch/run_travel_v1_platform.py` -> `evalforge_platform.db`
*   `scratch/run_travel_v1_single.py` -> `evalforge_platform_trace.db`
*   `scratch/test_failure_injection.py` -> `evalforge_platform_failure_test.db`
*   `scratch/test_passing_case.py` -> `evalforge_platform_passing_test.db`
*   `scratch/test_repeatability.py` -> `evalforge_platform_repeatability.db`
*   `scratch/validate_pipeline.py` -> `evalforge_platform.db`
*   `scratch/analyze_failures.py` -> `evalforge_failure_analysis.db`

### 4.4 Test Suite
*   [test_sqlite_repository.py](file:///d:/AI/evalforge/tests/unit/test_sqlite_repository.py): Directly tests SQLite repository.
*   [test_experiment_engine.py](file:///d:/AI/evalforge/tests/unit/test_experiment_engine.py): Tests experiment persistence via `SqliteEvaluationRepository`.
*   [test_e2e_evaluation.py](file:///d:/AI/evalforge/tests/integration/test_e2e_evaluation.py): Tests complete pipeline starting with SQLite repository.

---

## 5. Files to Change vs. Files NOT to Change

### Files That MUST Change:
1.  **[pyproject.toml](file:///d:/AI/evalforge/pyproject.toml) & [requirements.txt](file:///d:/AI/evalforge/requirements.txt)**: Add `psycopg2-binary` (PostgreSQL adapter).
2.  **[app.py](file:///d:/AI/evalforge/src/adapters/api/app.py)**:
    *   Add check for `DATABASE_URL` env variable.
    *   Dynamically instantiate `PostgresEvaluationRepository` if `postgresql://` is detected; otherwise, fallback to `SqliteEvaluationRepository`.
    *   Enhance `/health` endpoint to verify database connection health.
3.  **[__init__.py](file:///d:/AI/evalforge/src/adapters/repositories/__init__.py)**: Export new `PostgresEvaluationRepository`.

### Files That Are NEW:
1.  **`src/adapters/repositories/postgres_repository.py`**: Contains `PostgresEvaluationRepository` subclass of `EvaluationRepository`.
2.  **`scratch/migrate_sqlite_to_postgres.py`**: Script to backup the existing sqlite database and migrate all tables and relationships into PostgreSQL, verifying integrity.
3.  **`tests/integration/test_postgres_repository.py`**: Integration tests to verify insert, read, update, delete, transaction safety, and concurrency in PostgreSQL.
4.  **`docs/POSTGRES_MIGRATION_PLAN.md`**: Design plan.
5.  **`docs/POSTGRES_MIGRATION_REPORT.md`**: Final results report.

### Files That Must NOT Change (Strict Constraint):
1.  **Domain Entities** (`src/domain/entities/*.py`): Do not modify models (`GoldenDataset`, `EvaluationRun`, `Experiment`, `Trajectory`, `Step`, etc.) to keep evaluation schemas and logic intact.
2.  **Use Cases** (`src/use_cases/**/*.py`): All metrics calculators, judges, dataset validation logic, and report generation engines must remain untouched.
3.  **SUT Implementations** (`examples/travel_agent/travel_agent_sut.py`): The deterministic travel agent execution logic must not be modified.

---

## 6. Migration Risks & Mitigation

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **SQL Syntax Differences** | PostgreSQL does not support `INSERT OR REPLACE` or `?` placeholders. | Use standard `INSERT INTO ... ON CONFLICT (...) DO UPDATE` (upsert) and `%s` placeholders. |
| **Connection Pooling & Threading** | PostgreSQL requires active network connection management and is not file-based. | Use `psycopg2.pool.SimpleConnectionPool` or `ThreadedConnectionPool`. Execute blocking database calls within `asyncio.to_thread` to preserve the non-blocking FastAPI behavior. |
| **Schema Drift & Data Loss** | Storing JSON data differently could break backend serialization or frontend UX. | Retain identical schemas and serialize Pydantic structures to `TEXT` (or `JSONB`) exactly as they are currently stored. We will use `TEXT` in Postgres to ensure zero serialization changes. |
| **Connection Failure on Boot** | Render/Cloud deployments might boot app before DB is ready. | Implement startup retry/backoff logic in PostgreSQL repository initialization. |
| **Local Dev Friction** | Hardening for Postgres makes it hard for developers to run locally. | Automatically fallback to local SQLite if `DATABASE_URL` is not set or refers to SQLite. Provide a `docker-compose.yml` service for a local PostgreSQL database. |
| **Test Database Conflicts** | Tests running against production or dirtying dev db. | Configure test suite to use SQLite (`temp_db`) by default or a isolated temporary PostgreSQL schema if a dedicated test database URL is supplied. |

---

## 7. Recommended Migration Strategy

1.  **Preserve Interface Contracts**: Ensure `PostgresEvaluationRepository` satisfies every signature of `EvaluationRepository` so it can be swapped transparently into the FastAPI app, runner, and tests.
2.  **Graceful Database Fallback**: Read `DATABASE_URL`. If it contains `postgresql` or `postgres`, use PostgreSQL. Otherwise, use SQLite.
3.  **Controlled Data Migration**: Write a standard ETL script (`migrate_sqlite_to_postgres.py`) that opens both SQLite and PostgreSQL, extracts all records, handles syntax/placeholder differences, inserts them into PostgreSQL, and asserts table sizes and checksums.
4.  **No ORM Migration**: Avoid using heavy ORMs (like SQLAlchemy or Alembic) since the current database layer uses raw SQL queries and inline schema initialization. Introduce raw `psycopg2` implementation to match the existing SQL design.
