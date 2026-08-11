# EvalForge

**A benchmark-driven evaluation and observability platform for agentic AI systems.**

---

## Live Demo

Explore the deployed EvalForge application:

* **Frontend Dashboard**: [EvalForge UI](https://evalforge.vercel.app)
* **Backend API**: [EvalForge REST Server](https://evalforge-backend.onrender.com) *(Placeholder - replace with actual Render service URL if modified)*
* **Service Status**: [Backend Health Status](https://evalforge-backend.onrender.com/health) *(Placeholder - replace with actual Render health URL)*

> [!NOTE]
> Deployed live URLs can be updated in backend `.env` variables (`ALLOWED_ORIGINS`) and frontend `.env.local` variables (`NEXT_PUBLIC_API_URL`) to support live production environments.

---

## Overview

EvalForge is a model-agnostic, production-grade AI Agent Evaluation and Observability Platform designed to benchmark, audit, and inspect autonomous agents running in multi-turn, tool-using, and constraint-bound environments. 

Rather than treating evaluation as a simple assertion check, EvalForge treats it as a multi-dimensional observability pipeline. The platform allows machine learning and software engineers to define golden datasets containing expected tool calls, latency boundaries, cost budgets, and context guidelines, and then execute agents against these cases while compiling step-by-step reasoning trajectories. It evaluates outcomes via programmatic heuristics alongside cognitive LLM-as-a-judge rubrics, persists runs in a PostgreSQL instance, and displays comparative regression deltas in an interactive Next.js dashboard.

---

## Why EvalForge?

Traditional software testing follows a predictable path: a fixed inputs maps to a single codepath yielding a deterministic return value. Autonomous AI agents do not follow this pattern:
* **Statefulness**: An agent's action at step $N$ is dependent on observations returned by tools at steps $1$ to $N-1$.
* **Non-Determinism**: Even with `temperature=0.0`, prompts, models, and retrieval pipelines shift reasoning paths dynamically.
* **Tool Interactivity**: Agents autonomously determine which APIs to execute and format arguments dynamically, introducing execution error risks.
* **API Cost and Latency**: Complex multi-turn reasoning loops can trigger infinite loops or consume astronomical numbers of tokens, leading to budget overrun.

EvalForge provides a structured testing framework to isolate, debug, and prevent regressions in these agentic behaviors.

---

## Problem

Traditional software testing reduces verification to:

```
INPUT  ──>  SYSTEM  ──>  EXPECTED OUTPUT  ──>  PASS/FAIL
```

In agentic architectures, this simplified pass/fail signal is insufficient. An agent can return a response that matches the expected answer text, yet still fail along hidden dimensions:
* **Calling the wrong tool**: Fetching flight status via an SMS notification tool instead of a flight database search.
* **Incorrect arguments**: Passing unformatted dates or wrong city codes to search tools.
* **Ungrounded context**: Fabricating flight numbers or hotel rates not present in retrieved context records.
* **Violating constraints**: Satisfying the query but exceeding latency limits or token quotas.
* **Intermediate errors**: Encountering tool exceptions, retrying blindly, and wasting API costs before finding an answer.

Therefore, the critical engineering question is not only: *"Did the final answer pass?"*  
It is: ***"Did the agent follow the correct trajectory steps to resolve the query, and can we explain why it passed or failed?"***

EvalForge captures the complete intermediate execution trace, giving engineers the tools to diagnose structural failures inside agentic systems.

---

## Inspiration — Booking.com

EvalForge was inspired by the growing focus on AI-agent evaluation at Booking.com and the broader 2026 engineering problem of making GenAI systems measurable, testable, and reliable in production. Booking.com's public engineering and data-science work highlights the necessity of treating LLM evaluation as a quantitative engineering discipline rather than a simple validation check. 

Conceptual inspirations drawn from this space include:
1. Moving away from manual prompt verification to automated, run-based golden benchmarks.
2. Segmenting evaluation into multiple dimensions, isolating retrieval quality (context recall/precision) from reasoning validity (faithfulness).
3. The necessity of regression delta testing to guarantee that upgrading underlying models or prompt instructions does not degrade task reliability.

*Disclaimer: EvalForge is an independently implemented open-source project. It is not built, endorsed, or affiliated with Booking.com, and does not use any proprietary Booking.com data, systems, or source code.*

---

## What EvalForge Does

EvalForge manages the complete lifecycle of agent execution, from benchmark definition to visualization and regression analysis:

```
                    Benchmark Definition
                           |
                           v
                  Dataset / Test Cases
                           |
                           v
                 Benchmark Runner
                           |
                           v
                    Agent / SUT
                           |
              +------------+------------+
              |            |            |
              v            v            v
          Tool Calls   Retrieval     Response
              |         /Context        |
              +------------+------------+
                           |
                           v
                  Execution Trace
                           |
             +-------------+-------------+
             |                           |
             v                           v
     Deterministic Metrics         LLM Judges
             |                           |
             +-------------+-------------+
                           |
                           v
                  Evaluation Result
                           |
                           v
                      PostgreSQL
                           |
                           v
                   EvalForge UI/API
                           |
                           v
              Debug / Compare / Regress
```

---

## Key Capabilities

* **Pluggable System Under Test (SUT)**: Decoupled through an abstract `AgentSUT` interface. The framework logic contains no business details of reference applications.
* **Trajectory Traveral Tracing**: Records intermediate thoughts, tool calls, arguments, observations, costs, token usage, and latency per turn.
* **Multi-Dimensional Metrics**: Segregates deterministic heuristics (latency, cost, tokens, tool schemas) from qualitative cognitive evaluators.
* **Structured Output Judges**: Utilizes a rate-limit resilient parser that extracts JSON blocks from raw LLM responses, validates them using Pydantic, and retries on failure.
* **Dynamic persistence**: Automatically swaps between PostgreSQL (with pooling and URL sanitization) and SQLite.
* **Experiment Delta Analysis**: Tracks and compares metrics across multiple runs of an experiment to detect performance drifts.

---

## How It Works

1. **API Entry**: A client posts a run request to `/api/benchmarks/run`.
2. **Dataset Resolution**: The backend loads the registered `GoldenDataset` from database tables.
3. **Execution Delegation**: The FastAPI server offloads the benchmark to a background task runner thread to prevent blocking HTTP connections.
4. **Agent Execution**: The SUT is run against each test case concurrently (bounded by a semaphore). All intermediate thoughts, tool calls, and observations are appended to a `Trajectory` model.
5. **Metric Calculation**: Deterministic metrics check constraint thresholds (budget limits, tool names). Context Precision/Recall are calculated against ground-truth texts.
6. **Cognitive Grading**: If qualitative judges are configured, the trajectory is sent to `LLMJudgeEngine` nodes to grade groundedness and faithfulness.
7. **Persisting Outcomes**: Run records and trajectories are saved to PostgreSQL (or SQLite).
8. **Observability UI**: Next.js fetches data from the API and displays dashboard statistics, runs lists, and interactive step traces.

---

## Architecture

EvalForge is structured following **Clean Architecture** guidelines to isolate business logic from database, API, and LLM frameworks:

```
+-------------------------------------------------------------+
|                     Infrastructure Layer                    |
|       (FastAPI framework, database pools, logging, dotenv)  |
+------------------------------+------------------------------+
                               | (implements)
                               v
+-------------------------------------------------------------+
|                        Adapters Layer                       |
|   (PostgresRepository, SQLiteRepository, GeminiProvider,    |
|    OllamaProvider, OpenRouterProvider, API controllers)     |
+------------------------------+------------------------------+
                               | (implements / uses)
                               v
+-------------------------------------------------------------+
|                       Use Cases Layer                       |
|   (BenchmarkRunner, MetricRegistry, FaithfulnessEvaluator,  |
|    ExperimentEngine, AggregationEngine, LLMJudgeEngine)     |
+------------------------------+------------------------------+
                               | (uses)
                               v
+-------------------------------------------------------------+
|                         Domain Layer                        |
|   (EvaluationRun, GoldenDataset, GoldenTestCase, Trajectory,|
|    Step, ToolCall, LLMProvider / Repository contracts)      |
+-------------------------------------------------------------+
```

* **Domain Layer (`src/domain/`)**: Pure Pydantic models (no framework dependencies) defining core evaluation structures and interfaces.
* **Use Cases Layer (`src/use_cases/`)**: Rules orchestrating evaluations, running metrics, invoking judges, and calculating experiment deltas.
* **Adapters Layer (`src/adapters/`)**: Concrete integrations with databases (SQLite, Postgres), API routers, and LLM providers.
* **Infrastructure Layer (`src/infrastructure/`)**: Low-level logging configs and environment load scripts.

---

## Internal Execution Flow

The sequence diagram below details how the `BenchmarkRunner` coordinates evaluation sweeps asynchronously:

```
Client         FastAPI App      BenchmarkRunner      AgentSUT       Evaluators      Repository
  |                 |                  |                |               |               |
  |-- POST Run ---->|                  |                |               |               |
  |                 |-- Start Task --->|                |               |               |
  |<- run_id (202)-|                  |                |               |               |
  |                 |                  |-- run() ------>|               |               |
  |                 |                  |                |-- Call Tool ->|               |
  |                 |                  |                |<- Obs --------|               |
  |                 |                  |<-- Trajectory -|               |               |
  |                 |                  |                                |               |
  |                 |                  |-- Evaluate Trajectory -------->|               |
  |                 |                  |<-- Metric Scores --------------|               |
  |                 |                  |                                                |
  |                 |                  |-- Save Evaluation Run ------------------------>|
  |                 |                  |                                                |
```

---

## Evaluation Methodology

### Deterministic Metrics

Programmatic checks implemented in [evaluators.py](file:///d:/AI/evalforge/src/use_cases/metrics/evaluators.py) to assess structural constraints:
* **`Latency`**: Asserts SUT duration is below `latency_constraint` thresholds. Detects API delays or slow agent thought loops.
* **`TokenUsage`**: Audits prompt, completion, and total tokens against `token_constraint`. Prevents deployment budget overruns.
* **`Cost`**: Calculates financial cost in USD using model pricing indices, ensuring it stays under the `cost_constraint`.
* **`ToolCalling`**: Compares actual tool names and call order with `expected_tool_calls`. Detects tool-selection errors, formatting anomalies, and tool execution loop failures.
* **`ContextRecall`**: Computes string-overlap recall of retrieved context snippets against `ground_truth_context` lists. Measures retrieval system performance.
* **`ContextPrecision`**: Uses Average Precision (AP) formulas to score the relevance ranking of retrieved context snippets. Asserts that the most relevant information resides at the top.

### LLM-as-a-Judge

Cognitive evaluations orchestrated by the [LLMJudgeEngine](file:///d:/AI/evalforge/src/use_cases/judges/engine.py):
* **`Faithfulness`**: Rubric scoring whether every statement in the SUT response is supported *only* by retrieved context snippets. Detects context hallucination.
* **`Groundedness`**: Rubric scoring whether the response directly addresses the query and satisfies user tags. Detects task failures.
* **`AnswerCorrectness`**: Compares SUT outputs semantically against the ground-truth `expected_answer`. Detects logical deviations.
* **`Hallucination`**: Safety checker looking specifically for fabricated facts or context contradictions.

#### Why Heuristics and LLM Judges Complement Each Other
Programmatic checks capture **constraints and structure** (was a tool called, did we blow past token limits), whereas LLM Judges capture **meaning and alignment** (was the response accurate, did we invent facts). A fast agent with perfect tool calls can still hallucinate a bad answer; a slow agent with a perfect answer can still break operational latency rules. EvalForge unites both under a single evaluation schema.

---

## Benchmark Suite

EvalForge registers 10 static, version-controlled JSON datasets under the [datasets/](file:///d:/AI/evalforge/datasets) folder to test different classes of agent behaviors:

1. **`travel_v1`**: Baseline dataset (25 cases) covering flight queries, hotel reservations, and attraction searches.
2. **`travel_tool_calls`**: Stresses multi-turn tool chaining and complex JSON argument generation.
3. **`travel_regression`**: Repeatability baseline dataset used for delta comparison.
4. **`travel_safety`**: Checks response safety against instruction leaks, jailbreaks, and policy violations.
5. **`travel_adversarial`**: Contains customer requests with conflicting parameters or unrealistic budget constraints.
6. **`travel_edge_cases`**: Boundaries checking calendar overlaps, missing parameters, and format conversions.
7. **`travel_long_context`**: Stresses retrieval capacity using dense, multi-page context lookup inputs.
8. **`travel_missing_context`**: Focuses on hallucination suppression when search returns empty context blocks.
9. **`travel_multilingual`**: Validates agent query processing in Spanish, French, and other target locales.
10. **`travel_provider_benchmark`**: Standardized comparisons to grade underlying model capacities.

---

## Execution Traces

Checking final accuracy scores is insufficient for debugging. EvalForge exposes intermediate steps.

### Conceptual Trace Structure
```
 [User Request]
       │
       ▼
 [Step 1] thought: "Searching flights to Paris" ──> search_flights(origin="NYC", dest="PAR")
       │
       ▼
 [Observation] [Flight records JSON returned by tool]
       │
       ▼
 [Step 2] thought: "Checking policy boundaries" ──> check_policy(budget=250)
       │
       ▼
 [Observation] "Policy confirmed: Approved"
       │
       ▼
 [Step 3] thought: "Formatting response" ──> final_response: "Flight UA10 booked..."
       │
       ▼
 [Evaluation] Metric checks (latency, tokens, tool names) & LLM Judge scores.
```

Through the **Trajectory Trace Inspector** panel in the UI, developers can isolate exactly where an execution failed, verifying if the issue was a tool failure, context retrieval error, or reasoning hallucination.

---

## Experiments and Run History

EvalForge organizes runs into experiments to allow historical comparison and delta analysis.

### Case Study Scenario: Upgrading Retrieval Strategies

```
      Baseline (Version A)                      Current (Version B)
      Dataset: travel_v1                        Dataset: travel_v1
      Retrieval: Vector search only             Retrieval: Hybrid + Re-ranking
      
   +---------------------------+             +---------------------------+
   |  Success Rate:  92.0%     |             |  Success Rate:  84.0%     |
   |  Avg Latency:   1.8s      |   ─────>    |  Avg Latency:   2.4s      |
   |  Avg Cost:      $0.005    |  (Delta)    |  Avg Cost:      $0.008    |
   |  ContextRecall: 0.95      |             |  ContextRecall: 0.82      |
   +---------------------------+             +---------------------------+
```

Although Hybrid search was expected to perform better, Version B caused a success rate regression (92% down to 84%) and increased average latency (1.8s up to 2.4s). The `ExperimentEngine` highlights these changes, pointing the engineer to the exact test cases where retrieval precision dropped.

---

## Technology Stack

* **Core Language**: Python 3.11+
* **Backend Framework**: FastAPI (Uvicorn server)
* **Frontend Framework**: Next.js React (TypeScript)
* **Primary Database**: PostgreSQL (Render Cloud / Local Docker)
* **Development Database**: SQLite (Fallback)
* **HTTP & Database Client**: Psycopg2-binary, HTTPX
* **Data Validation**: Pydantic v2
* **Visualization Utilities**: Recharts, Rich logging
* **LLM Providers**: Gemini, Ollama, OpenRouter

---

## Why This Tech Stack?

* **Python**: The standard language for AI systems development, parsing, and LLM SDK integration.
* **FastAPI**: Selected for its asynchronous capabilities, auto-generated Swagger documentation, and background task integration.
* **PostgreSQL**: Selected as the durable persistent store to maintain large JSON execution trajectories and allow concurrent queries.
* **Psycopg2**: Used for high-speed connection management.
* **Next.js & React**: Provides server-side layout pre-rendering and clean state-management for dashboard comparisons.
* **TypeScript**: Enforces strict payload formatting contracts between the backend JSON payloads and frontend display nodes.
* **LLM Providers (Gemini / Ollama / OpenRouter)**: Enables model-agnostic evaluations. Ollama supports local, cost-free developer testing, Gemini provides fast cloud performance, and OpenRouter supports model testing sweeps.

---

## Database Architecture

EvalForge uses identical column structures in SQLite and PostgreSQL to prevent serialization mismatches:

### `golden_datasets`
* `dataset_id` (TEXT)
* `version` (TEXT)
* `name` (TEXT)
* `description` (TEXT)
* `test_cases` (TEXT): JSON-serialized array of `GoldenTestCase` objects.
* `metadata` (TEXT): JSON-serialized dictionary of metadata.
* **Primary Key**: `(dataset_id, version)`
* **Index**: `idx_datasets_id` on `(dataset_id)`

### `evaluation_runs`
* `run_id` (TEXT) - Primary Key
* `dataset_id` (TEXT)
* `dataset_version` (TEXT)
* `sut_version` (TEXT)
* `timestamp` (TEXT): ISO-8601 string representation.
* `cases` (TEXT): JSON-serialized array of `TestCaseEvaluation` objects (which stores steps, tool calls, and metric results).
* `parameters` (TEXT): JSON-serialized execution parameters.
* `summary` (TEXT): JSON-serialized run summaries.
* `metadata` (TEXT): JSON-serialized metadata.
* **Index**: `idx_runs_dataset` on `(dataset_id)`

### `experiments`
* `experiment_id` (TEXT) - Primary Key
* `name` (TEXT)
* `description` (TEXT)
* `run_ids` (TEXT): JSON-serialized array of run ID strings.
* `metadata` (TEXT): JSON-serialized metadata.
* `created_at` (TEXT): ISO-8601 string representation.

---

## SQLite → PostgreSQL Migration

To scale EvalForge from local developer testing to shared staging deployments, the persistence layer was upgraded from a single-file SQLite database to PostgreSQL.

### Connection Management and Transaction Safety
The `PostgresEvaluationRepository` uses a thread-safe connection pool `psycopg2.pool.ThreadedConnectionPool` (configured to support 1 to 20 connections) to prevent resource contention. Database transactions are isolated using a context manager helper:

```python
from contextlib import contextmanager

@contextmanager
def _get_connection(self):
    """Context manager to acquire a connection from the pool and yield it."""
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

* **Scheme Sanitization**: Connection strings are checked at startup. If a cloud provider supplies a `postgres://` prefix, it is sanitized to `postgresql://` to prevent driver errors.
* **Graceful Fallback**: If the `DATABASE_URL` environment variable is missing or invalid, EvalForge falls back to SQLite (`evalforge_platform.db`), keeping local setups friction-free.

### Data Migration CLI Utility
The ETL script [migrate_sqlite_to_postgres.py](file:///d:/AI/evalforge/scratch/migrate_sqlite_to_postgres.py) copies SQLite records into PostgreSQL:
1. **Safety Backup**: Backs up the SQLite database file (`evalforge_platform.db.backup`).
2. **Schema Verification**: Runs SQL table creations in the Postgres target database before running inserts.
3. **Conflict Resolution**: Inserts dataset, run, and experiment records using `ON CONFLICT DO UPDATE` (upsert) statements to avoid duplicate PK errors.
4. **Integrity Check**: Verifies table row counts, raising an exception if mismatching checksums are detected.

---

## API

### Swagger UI Docs
* **Interactive OpenAPI docs**: `/docs`
* **Static API reference**: `/redoc`

### Primary API Routes

| Method | Path | Purpose | Query / Body Parameters | Response |
| :--- | :--- | :--- | :--- | :--- |
| **`GET`** | `/health` | Verifies database connectivity and returns database type. | None | `{ "status": "healthy", "database": "postgresql" }` |
| **`GET`** | `/api/datasets` | Lists all registered datasets. | None | Array of dataset descriptions and case counts. |
| **`POST`** | `/api/datasets` | Registers a new Golden Dataset. | JSON Dataset schema | `{ "status": "registered", "dataset_id": "..." }` |
| **`POST`** | `/api/benchmarks/run` | Triggers a benchmark run asynchronously. | `{ "dataset_id": "...", "version": "...", "concurrency": 3 }` | `{ "status": "running", "run_id": "run-..." }` |
| **`GET`** | `/api/runs` | Lists historical benchmark runs. | None | Array of run IDs, timestamps, and summary stats. |
| **`GET`** | `/api/runs/{run_id}` | Retrieves execution trajectories and metrics. | `run_id` (Path) | Full evaluation run JSON including case step trace lists. |
| **`GET`** | `/api/experiments` | Lists registered experiments. | None | Array of experiments and run counts. |
| **`GET`** | `/api/experiments/{experiment_id}` | Retrieves experiment deltas and reports. | `experiment_id` (Path) | Experiment details and delta comparison markdown. |

---

## How to Explore the Live Demo

Follow these steps to explore the deployed EvalForge application:

1. **Check System Health**:
   * Open the [Backend Health Status](https://evalforge-backend.onrender.com/health) page in your browser. Confirm that `"database"` reports `"postgresql"` and `"status"` is `"healthy"`.
2. **Inspect Datasets**:
   * Navigate to the **Datasets** tab on the [EvalForge UI](https://evalforge.vercel.app). Check the available benchmark suites (e.g., `travel_v1`). Expand a suite to inspect its case categories, queries, expected tool calls, and constraints.
3. **Audit Run History**:
   * Open the **Run History** tab. Select a historical benchmark run (e.g., the `run-a0aa7aa3` validation sweep). Inspect the aggregated statistics cards showing overall success rate, latency averages, and USD costs.
4. **Trace Trajectories**:
   * Scroll down the run details and click on a test case (such as case `001` or `010`). Inspect the **Trajectory Trace Inspector** to view intermediate agent thoughts, parameters sent to tool APIs, observations returned, and LLM judge justifications.
5. **Run a Benchmark**:
   * Navigate to the **Overview** tab. Select a dataset, set the SUT concurrency (e.g., `3`), set max retries to `0`, and click **Launch Benchmark Run**. The status will display as "running" and update reactively as cases complete.

---

## Local Development

### Prerequisites
* **Python**: Version 3.11+
* **Node.js**: Version 18+
* **Docker**: Required for local PostgreSQL service testing (optional)

### Setup Instructions

#### 1. Setup Backend API
Activate virtual environment and install packages:
```powershell
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

Create a root `.env` configuration file matching the environment templates:
```env
GEMINI_API_KEY=your_gemini_api_key
OLLAMA_API_BASE=http://localhost:11434
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evalforge
ALLOWED_ORIGINS=http://localhost:3000
```

Start the FastAPI application:
```powershell
python -m uvicorn src.adapters.api.app:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Setup Frontend UI
Navigate to `frontend/`, install node modules, and start dev server:
```powershell
cd frontend
npm install
npm run dev
```
Open http://localhost:3000 to view the interface.

#### 3. Run with Docker Compose
To run PostgreSQL, backend, and frontend containers automatically:
```powershell
docker-compose up --build
```

---

## Environment Variables

### Backend Configuration (`.env`)
* `DATABASE_URL` (Optional): Connection string for PostgreSQL database. If empty, fallback SQLite (`evalforge_platform.db`) is used.
* `GEMINI_API_KEY` (Required for Gemini): API key for Gemini LLM models.
* `OLLAMA_API_BASE` (Optional): Target address for local Ollama server. Default: `http://localhost:11434`.
* `OPENROUTER_API_KEY` (Optional): API key for OpenRouter integrations.
* `ALLOWED_ORIGINS` (Optional): CORS configuration comma-separated string of accepted host origins.

### Frontend Configuration (`frontend/.env.local`)
* `NEXT_PUBLIC_API_URL` (Required): Target URL of the backend FastAPI endpoint. Local default: `http://localhost:8000`.

---

## Testing

Verify code quality and type alignments using the testing suites:

```powershell
# 1. Format Verification
python -m black --check src tests

# 2. Pattern Linting
python -m ruff check src tests

# 3. Static Type Verification
python -m mypy src tests

# 4. Execute Complete Pytest Suite
python -m pytest
```

### What the Test Suite Protects Against
* **API Breakages**: Verifies FastAPI endpoint responses and CORS origin header rejections.
* **PostgreSQL Concurrency Limits**: Asserts that concurrent database writes do not exhaust the connection pool or trigger deadlock errors.
* **Registry Duplicates**: Prevents naming collisions when registering new metrics or cognitive judges.
* **LLM Judge Fault Fallbacks**: Asserts that when LLM judges return conversational text instead of JSON, the parsing regex extracts correct values and validates schemas properly.

---

## Production Deployment

EvalForge is deployed using Vercel for the static frontend and Render for the API services:

```
               [ User Web Browser ]
                        │
                        ▼ (HTTPS)
            +───────────────────────+
            │   Vercel Deployment   │
            │   (Next.js Frontend)  │
            +───────────┬───────────+
                        │
                        │ API Queries (CORS validation)
                        ▼
            +───────────────────────+
            │   Render Deployment   │
            │   (FastAPI Backend)   │
            +───────────┬───────────+
                        │
                        ▼ (SQL pool)
            +───────────────────────+
            │   Render PostgreSQL   │
            │    (Database Node)    │
            +───────────────────────+
```

* **CORS Policies**: The backend's `ALLOWED_ORIGINS` is configured to target the Vercel app domain, rejecting other unauthorized domain headers.
* **Database Url Conversions**: The backend handles Render database string updates internally, sanitizing the connection schema before establishing psycopg2 connections.

---

## Challenges & Engineering Decisions

### 1. PostgreSQL Schema Mapping and Syntax Divergence
* **Problem**: SQLite supports `INSERT OR REPLACE` and `?` query placeholders. PostgreSQL does not, throwing syntax exceptions on the original adapter code.
* **Cause**: SQLite and PostgreSQL follow distinct SQL standards for conflict resolution and query bindings.
* **Decision**: Implement a separate `PostgresEvaluationRepository` implementing the abstract `EvaluationRepository` interface.
* **Fix**: Rewrote SQL statements in the PostgreSQL repository to use standard `%s` placeholders and `ON CONFLICT (PK) DO UPDATE SET` upsert syntax.
* **Learning**: Decoupling database queries into adapter implementations keeps core business code independent of database syntax differences.

### 2. Async Event Loop Blockage from Database Operations
* **Problem**: FastAPI's async loops would block when executing database writes, causing concurrent HTTP requests to time out.
* **Cause**: Python's standard `sqlite3` and `psycopg2` drivers are blocking (synchronous) libraries.
* **Decision**: Offload database adapter calls to separate worker threads.
* **Fix**: Wrapped all repository CRUD execution blocks in `asyncio.to_thread` functions inside both SQL adapters.
* **Learning**: Running blocking driver I/O on distinct threadpool workers preserves the non-blocking execution of the FastAPI async event loop.

### 3. Connection Exhaustion under Concurrency
* **Problem**: High-concurrency benchmark runs (e.g. running 10 test cases in parallel) would crash with connection errors.
* **Cause**: Spawning thread pools without pooling database connections caused database server connection limits to be exceeded.
* **Decision**: Introduce a thread-safe connection pooling system.
* **Fix**: Configured `psycopg2.pool.ThreadedConnectionPool` on backend boot, and implemented a clean context manager that releases connections back to the pool in a `finally` block even when errors occur.
* **Learning**: Bounding connection counts via a context-managed pool is necessary to guarantee database stability under concurrent execution stress.

### 4. Pydantic-to-TypeScript Contract Alignment
* **Problem**: Next.js dashboard components would crash when loading evaluation runs, throwing type errors.
* **Cause**: Pydantic serialized metric results as dictionaries (`dict[str, MetricResult]`), whereas the TypeScript frontend expected list arrays for map rendering.
* **Decision**: Standardize payload mapping at the API layer.
* **Fix**: Intercepted the returned model payload in the FastAPI router `/api/runs/{run_id}` to serialize dictionary values into standard list shapes before returning the JSON response.
* **Learning**: Normalizing payload shapes at the API controller boundary prevents type-mismatch crashes on frontend dashboard clients.

### 5. Integration Test Isolation and Database Cleaning
* **Problem**: Running PostgreSQL repository integration tests would dirty local development database tables, causing subsequent runs or experiments to report wrong metrics.
* **Cause**: Test assertions were running against the same database schema used for development.
* **Decision**: Implement clean table isolation fixtures.
* **Fix**: Created a `clean_db` fixture in `test_postgres_repository.py` that executes a `TRUNCATE ... CASCADE` script before and after every test, ensuring a clean isolated database state for assertions.
* **Learning**: Cleaning up persistent databases using transaction truncation fixtures is necessary to guarantee test repeatability.

---

## What I Learned

1. **Evaluation Trajectories are Critical**: Testing AI agents requires inspecting the *intermediate steps* (retrieval quality, tool call structure, reasoning), not just verifying final string outcomes.
2. **Deterministic and Cognitive Metrics Complement Each Other**: Programmatic checkers evaluate budget boundaries, whereas LLM Judges grade language accuracy. They solve distinct problems.
3. **Database Portability requires Abstraction**: Wrapping database operations in repository interfaces is the only way to support SQLite and PostgreSQL side-by-side without duplicating business code.
4. **Async Runtimes Need Thread Offloading**: Standard relational database drivers run synchronously. Offloading these queries using `asyncio.to_thread` is necessary to maintain non-blocking API performance.
5. **Data Migration Requires Validation**: Writing ETL scripts requires verifying row counts and checksums at completion. Blind copying risks silent encoding failures.

---

## Limitations & Future Work

* **Task Queue Distribution**: Current benchmarks run on local FastAPI background task threads. In production, this should be offloaded to a distributed task queue (like Celery or Redis Workers).
* **Trajectory Streaming**: The Next.js dashboard polls `/api/runs` to update trace details. Implementing WebSockets or Server-Sent Events (SSE) would allow live trace streaming.
* **Authentication & RBAC**: The platform has no security boundary. Future work should introduce OAuth2 and Role-Based Access Control (RBAC) to restrict access.
* **Automated CI/CD Gating**: Running evaluations as PR checks to block code commits that trigger regression deltas.

---

## Project Status

**Completed & Stable**. The evaluation framework, PostgreSQL repository connection pool, dataset and experiment engines, Next.js workspace tabs, and logging modules are fully implemented, verified, and green.

---

## License

This project is licensed under the MIT License. See package configuration files for license attributes.
