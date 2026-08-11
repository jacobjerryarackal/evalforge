# EvalForge — Benchmark-Driven Evaluation & Observability Platform for Agentic AI Systems

EvalForge is a model-agnostic, production-grade AI Agent Evaluation and Observability Platform designed to benchmark, audit, and observe autonomous agents running in complex, multi-turn, constraint-bound environments.

---

## 1. Value Proposition
**Verify agent reasoning, safety, and constraints before deploying to production.**  
EvalForge captures multi-turn agent execution trajectories, executes deterministic performance and retrieval metrics alongside Pydantic-validated cognitive LLM judges, tracks regression deltas across experimental runs, and persists structured results to PostgreSQL or SQLite.

---

## 2. Strong Opening Explanation
Building AI agents is easy, but ensuring their reliability in production is exceptionally difficult. Unlike traditional software systems which behave deterministically, AI agents operate non-deterministically, interact with dynamic third-party tools, maintain state across multi-turn sessions, and are vulnerable to specific failure modes such as infinite execution loops, instruction leakage, hallucinated actions, and budget/token overrun.

### Why Ordinary Pass/Fail Testing is Insufficient
Traditional testing frameworks verify assertions on a final state or a single output value. However, an agentic AI system can produce a seemingly correct final answer while failing along multiple unobserved dimensions:
1. **Calling the wrong tool** (e.g., executing a booking service instead of a query service).
2. **Utilizing incorrect context** (e.g., grounding reasoning on stale flight records).
3. **Violating operational constraints** (e.g., exceeding budget limits or latency constraints).
4. **Exhibiting specific safety failures** (e.g., leaking instructions or bypassing corporate policy).

EvalForge goes beyond simple final-answer pass/fail grading. It records and audits the **execution trajectory** (reasoning thoughts, tool calls, arguments, observations, and system costs) of the agent, providing a complete observability audit trail.

---

## 3. Key Capabilities
* **Pluggable Evaluation Engine**: Completely decoupled from both the System Under Test (SUT) and the LLM API provider.
* **Execution Trajectory Tracing**: Records each turn of agent reasoning, including thoughts, tool inputs, execution outcomes, costs, token usage, and latency.
* **Deterministic Performance Metrics**: Programmatic evaluators for Latency, Token Usage, Cost budgets, and Tool Call schemas.
* **Retrieval Metric Suite**: Evaluates RAG quality via context precision ranking and context recall heuristics against ground truth databases.
* **Pydantic-Validated LLM Judges**: Implements robust, rate-limited cognitive evaluation rubrics for Faithfulness, Groundedness, Answer Correctness, and Hallucination.
* **Experimentation & Delta Regression Tracking**: Group runs into experiments to calculate changes in latency, cost, and success rate, detecting regressions over time.
* **Production Persistence Adapter**: Integrates with PostgreSQL (featuring thread-safe connection pooling and automatic url scheme sanitization) and falls back to SQLite.
* **Dual-Service Workspace**: Serves REST APIs over FastAPI backend and displays comparisons, triggers, and trace breakdowns in a Next.js TypeScript UI.
* **Structured JSON Observability**: Outputs structured, machine-parseable JSON lines logging for direct ingestion into logging pipelines.

---

## 4. "Why EvalForge?"
The table below contrasts the paradigms of development-grade unit testing and production-grade agentic evaluation:

| Feature / Dimension | Traditional Pass/Fail Testing | Agent Evaluation (EvalForge) |
| :--- | :--- | :--- |
| **Execution Path** | Single input maps to a predictable, mocked code path. | Multi-turn, non-deterministic agent loop with dynamic tool selection. |
| **Verification Scope** | Checks final state or return value correctness. | Observes and grades the entire trajectory, including thoughts, tool calls, and grounding. |
| **Performance Constraints** | Simple timeout checks. | Tracks tokens, costs, tool execution success, and multi-turn budgets. |
| **Cognitive Quality** | Brittle text similarity assertions (e.g., BLEU, ROUGE). | Semantic LLM-as-a-judge rubrics validating reasoning accuracy. |
| **Regression Analysis** | Code changes break tests directly. | Code, prompt, or model changes shift success rates, latencies, and costs dynamically. |

---

## 5. Concrete Evaluation Example
The following is a realistic benchmark test case defined in [datasets/travel_v1.json](file:///d:/AI/evalforge/datasets/travel_v1.json):

```json
{
  "id": "travel_v1_001",
  "difficulty": "Easy",
  "category": "flight",
  "user_query": "I need a flight from New York to London on August 15, 2026.",
  "retrieved_context": "Flights from JFK to LHR on Aug 15: British Airways BA112 departs 10:30, arrives 22:15, $850. Delta DL4 departs 08:00, arrives 20:30, $920. Both have 1 stop.",
  "expected_tool_calls": [
    {
      "service": "FlightService",
      "method": "search_flights",
      "parameters": {
        "origin": "NYC",
        "destination": "LON",
        "date": "2026-08-15"
      }
    }
  ],
  "expected_answer": "British Airways BA112 at 10:30, arriving 22:15, $850, or Delta DL4 at 08:00, arriving 20:30, $920.",
  "latency_constraint": 2.0,
  "token_constraint": 200,
  "cost_constraint": 0.01,
  "expected_metrics": {
    "context_precision": 1.0,
    "context_recall": 1.0
  },
  "expected_judge_scores": {
    "faithfulness": 1.0,
    "groundedness": 1.0,
    "correctness": 1.0,
    "hallucination": 0.0
  },
  "failure_mode": "None"
}
```

In this case, an agent fails if it:
* Fails to execute `search_flights` with origin `NYC` and destination `LON`.
* Exceeds `2.0` seconds in latency, `200` total tokens, or `$0.01` in cost.
* Hallucinates flights not listed in the retrieved context (scored by the Hallucination LLM judge).
* Answers with details contradicting the retrieved context (scored by the Faithfulness LLM judge).

---

## 6. Architecture Flow
The ASCII diagram below illustrates the flow of dataset inputs, SUT execution, metric calculation, and visualization inside EvalForge:

```
                             +--------------------+
                             |   Golden Dataset   |
                             +---------+----------+
                                       |
                                       | (JSON/JSONL Cases)
                                       v
                             +--------------------+
                             |  Benchmark Runner  |
                             +----+----------+----+
                                  |          ^
                 (input_query)    |          | (Trajectory)
                                  v          |
                             +---------------+----+
                             | System Under Test  |
                             |    (Agent SUT)     |
                             +--------------------+
                                       |
                                       | (Steps & Traces)
                                       v
                             +--------------------+
                             | Evaluation Engine  |
                             +----+----------+----+
                                  |          |
              +-------------------+          +-------------------+
              |                                                  |
              v                                                  v
 +--------------------------+                      +--------------------------+
 |  Deterministic Metrics   |                      |     LLM Judge Engine     |
 |  - Latency, Token, Cost  |                      |  - Faithfulness, Grounded|
 |  - ToolCalling, Recall   |                      |  - Correctness, Hallucin.|
 |  - Context Precision     |                      |  - Structured JSON Parser|
 +------------+-------------+                      +------------+-------------+
              |                                                  |
              +-------------------+          +-------------------+
                                  |          |
                                  v          v
                             +--------------------+
                             | Aggregation Engine |
                             +---------+----------+
                                       |
                                       v
                             +--------------------+
                             | Persistence Layer  |
                             | (Postgres/SQLite)  |
                             +---------+----------+
                                       |
                                       v
                             +--------------------+
                             | EvalForge UI / API |
                             +--------------------+
```

---

## 7. Evaluation Lifecycle
The lifecycle of an evaluation run contains the following phases:
1. **Triggering**: A run is initiated via REST API (`POST /api/benchmarks/run`) or Next.js, specifying `dataset_id`, `version`, SUT identifier, and optional experiment metadata.
2. **Background Execution**: FastAPI validates the request and offloads execution to an asynchronous background task pool, returning a unique `run_id` immediately.
3. **SUT Run & Tracing**: The `BenchmarkRunner` maps test cases concurrently (bounded by a concurrency semaphore). SUT exceptions trigger configurable exponential backoff retries.
4. **Trajectory Compilation**: All thoughts, tool parameters, observations, latency, and costs are compiled into a `Trajectory` domain entity.
5. **Metrics & Judging Evaluation**:
   * Deterministic metrics analyze constraints, tool execution success, and context overlap.
   * LLM judges evaluate semantic rubrics, running prompt-compiled queries with `temperature=0.0` for consistency.
6. **Case Success Assertion**: A test case is declared `successful` ONLY if it didn't crash, did not violate token/latency/cost limits, and achieved score thresholds defined in the test case.
7. **Aggregation & Persistence**: The `AggregationEngine` compiles stats (average latency, total costs, success rate). The results are saved to the persistent database, and markdown reports are generated.

---

## 8. Benchmark Suite
The repository includes 10 static, version-controlled JSON datasets under the [datasets/](file:///d:/AI/evalforge/datasets) folder representing different test profiles:

| Dataset Name | Filename | Purpose / Focus |
| :--- | :--- | :--- |
| **Travel V1 Baseline** | [travel_v1.json](file:///d:/AI/evalforge/datasets/travel_v1.json) | Baseline flight, hotel, and attraction search scenarios (25 cases). |
| **Tool Calling Suite** | [travel_tool_calls.json](file:///d:/AI/evalforge/datasets/travel_tool_calls.json) | Focuses on multi-turn tool chaining and parameter validation constraints. |
| **Edge Cases** | [travel_edge_cases.json](file:///d:/AI/evalforge/datasets/travel_edge_cases.json) | Boundaries, invalid inputs, calendar overlaps, and format errors. |
| **Safety Suite** | [travel_safety.json](file:///d:/AI/evalforge/datasets/travel_safety.json) | Prompts for injection, system instruction leaks, and policy violations. |
| **Long Context** | [travel_long_context.json](file:///d:/AI/evalforge/datasets/travel_long_context.json) | Large, dense context lookup sweeps testing retrieval reasoning. |
| **Missing Context** | [travel_missing_context.json](file:///d:/AI/evalforge/datasets/travel_missing_context.json) | Empty or incomplete details testing hallucination suppression. |
| **Adversarial Queries** | [travel_adversarial.json](file:///d:/AI/evalforge/datasets/travel_adversarial.json) | Conflicting customer instructions and budget limitations. |
| **Multilingual Support** | [travel_multilingual.json](file:///d:/AI/evalforge/datasets/travel_multilingual.json) | Evaluates query handling in non-English contexts (French, Spanish, etc.). |
| **Regression Suite** | [travel_regression.json](file:///d:/AI/evalforge/datasets/travel_regression.json) | Repeatability baselines for delta comparison. |
| **Provider Benchmark** | [travel_provider_benchmark.json](file:///d:/AI/evalforge/datasets/travel_provider_benchmark.json) | Broad model capacity benchmarks across provider nodes. |

---

## 9. Evaluation Methodology

### Deterministic & Retrieval Metrics
Implemented in [evaluators.py](file:///d:/AI/evalforge/src/use_cases/metrics/evaluators.py):
* **`Latency`**: Asserts that execution duration is below the configured `latency_constraint` limit.
* **`TokenUsage`**: Asserts that total tokens consumed are within `token_constraint` boundaries.
* **`Cost`**: Calculates actual USD cost and verifies it is below the case's `cost_constraint` limit.
* **`ToolCalling`**: Audits tool status flags, checks if expected methods were called, and halts on execution loop triggers.
* **`ContextRecall`**: Computes text-overlap recall of retrieved context snippets against ground truth contexts.
* **`ContextPrecision`**: Evaluates context ranking using Average Precision (AP) against reference items.

### Qualitative LLM Judges
Orchestrated by the [LLMJudgeEngine](file:///d:/AI/evalforge/src/use_cases/judges/engine.py):
* **`Faithfulness`**: Rubric checking if the SUT response relies *only* on context and contains no unsupported assertions.
* **`Groundedness`**: Rubric checking if the response addresses the user query and conforms to user profile rules.
* **`AnswerCorrectness`**: Compares the SUT response semantically against the `expected_answer` reference output.
* **`Hallucination`**: Scans response strictly for factual fabrications or contexts contradictions.

> [!TIP]
> The `LLMJudgeEngine` enforces structured output parsing. It attempts JSON generation first. If validation fails, it applies a regex JSON block extractor to parse text fallbacks and retries on errors up to a retry limit.

---

## 10. Execution Traces
EvalForge tracks a complete, turn-by-turn trace history. Within the Next.js visual workspace, engineers can inspect:
* **Thought process**: The internal reasoning steps generated by the agent.
* **Tool inputs & outputs**: The exact argument dictionary passed to external APIs and the returned JSON observations.
* **Turn-by-turn latency & cost**: Micro-metrics for each individual step to isolate bottleneck queries.
* **Judge reasoning text**: Detailed step-by-step justifications compiled by the LLM judges explaining *why* a specific score was awarded.

---

## 11. Experiments and Run History
EvalForge organizes runs into experiments to allow historical comparison and delta analysis.
The [ExperimentEngine](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py):
* Stores groups of runs associated with a specific experiment configuration.
* Correlates performance and computes deltas (accrued variations in success rates, latencies, tokens, and budgets) against the first run of the experiment (the baseline).
* Compiles comparative markdown reports highlighting accuracy drifts or latency shifts.

---

## 12. Technical Architecture
EvalForge is organized according to **Clean Architecture** boundaries where dependencies point strictly inwards:

```
[Domain Layer] (Pure entities, value objects, interfaces)
     ^
     | (imported by)
[Use Cases Layer] (BenchmarkRunner, evaluators, judges, engines)
     ^
     | (imported by)
[Adapters Layer] (PostgreSQL/SQLite repos, LLM providers, FastAPI app)
     ^
     | (configured by)
[Infrastructure Layer] (Logging formatter, configuration loaders)
```

* **Frontend**: TypeScript, Next.js, and Recharts visualization.
* **Backend**: FastAPI, AsyncIO task delegation, Pydantic v2 data models.

---

## 13. Database and Persistence
EvalForge supports a dual-persistence strategy:
1. **PostgreSQL (`PostgresEvaluationRepository`)**:
   * Uses thread-safe connection pooling via `ThreadedConnectionPool` (supporting 1 to 20 concurrent connections).
   * Automatically sanitizes connection string prefixes (`postgres://` is translated to `postgresql://` to prevent driver errors on platforms like Render or Heroku).
   * Executes blocking database operations within `asyncio.to_thread` to preserve FastAPI event loop non-blocking performance.
2. **SQLite (`SqliteEvaluationRepository`)**:
   * Fallback engine if `DATABASE_URL` is empty or unset.
   * Persists database records in a single local database file (`evalforge_platform.db`).

### Database Migration CLI Utility
To transfer data from the local SQLite database to PostgreSQL, execute the ETL script:
```powershell
python scratch/migrate_sqlite_to_postgres.py <path_to_sqlite_db> <postgres_connection_url>
```
* The script creates a file-level SQLite safety backup before starting.
* Performs database table migrations with `ON CONFLICT DO UPDATE` (upsert) queries.
* Asserts matching row checksums between tables, ensuring data integrity.

---

## 14. API Endpoints
The backend FastAPI application exposes the following REST endpoints:

* **`/health` (GET)**: Performs connectivity queries against active databases (SQLite or PostgreSQL) and returns status.
* **`/api/datasets` (GET/POST)**: Lists registered datasets or registers new golden datasets (validates SemVer formats).
* **`/api/runs` (GET)**: Lists previous evaluation sweeps, timestamp records, and summaries.
* **`/api/runs/{run_id}` (GET)**: Retrieves detailed trajectory logs, step-by-step tool observations, and metric results.
* **`/api/experiments` (GET/POST)**: Lists or creates experiments.
* **`/api/experiments/{experiment_id}` (GET)**: Computes deltas and compiles comparative markdown summaries.
* **`/api/benchmarks/run` (POST)**: Triggers an evaluation run asynchronously via background task threads, returning a `run_id` instantly.

---

## 15. Local Development Setup

### Backend Setup
1. Requirements: **Python 3.11+**.
2. Activate a virtual environment:
   ```powershell
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create a `.env` file at the root:
   ```env
   GEMINI_API_KEY=your_gemini_key_here
   OLLAMA_API_BASE=http://localhost:11434
   OPENROUTER_API_KEY=your_openrouter_key_here
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evalforge
   ```
5. Run the FastAPI development server:
   ```powershell
   python -m uvicorn src.adapters.api.app:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup
1. Requirements: **Node.js 18+**.
2. Navigate to the `frontend/` directory:
   ```powershell
   cd frontend
   ```
3. Install dependencies:
   ```powershell
   npm install
   ```
4. Run the Next.js development server:
   ```powershell
   npm run dev
   ```
5. Open the UI: http://localhost:3000

---

## 16. Multi-Container Docker Build
To spin up PostgreSQL, the backend API, and the Next.js UI concurrently:
```powershell
docker-compose up --build
```
* **Frontend**: http://localhost:3000
* **Backend**: http://localhost:8000

---

## 17. Environment Variables
Below is the complete list of system environment variables:

| Variable | Type | Description | Default |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | String | Connection string for PostgreSQL database. | Fallback to local SQLite |
| `GEMINI_API_KEY` | String | API key for Gemini models. | Required for Gemini provider |
| `OLLAMA_API_BASE` | String | Base URL for Ollama local provider. | `http://localhost:11434` |
| `OPENROUTER_API_KEY` | String | API key for OpenRouter models. | Optional |
| `ALLOWED_ORIGINS` | String | CORS allowed origins split by commas. | `*` |

---

## 18. Testing
Verify repository code quality using the automated tools:

### Code Formatting Check
```powershell
python -m black --check src tests
```

### Linter Audit
```powershell
python -m ruff check src tests
```

### Static Type Checks
```powershell
python -m mypy src tests
```

### Test Suites Execution
Run all unit and integration tests (including PostgreSQL integrations):
```powershell
python -m pytest
```

---

## 19. Production Deployment
* **Backend (Render)**: Set the start command to launch uvicorn and supply the database connection URL in `DATABASE_URL`. Set CORS origins using `ALLOWED_ORIGINS`.
* **Frontend (Vercel)**: Build settings run Next.js build. Supply `NEXT_PUBLIC_API_URL` pointing to the Render backend address.

---

## 20. Engineering Decisions & Design Principles
* **Separation of Concerns**: Core modules contain no business details of reference applications (`examples/travel_agent/`).
* **Registry Pattern**: Metric and Judge registries manage modular discovery, enabling developers to add new evaluators without touching the runner.
* **Fault Shielding**: Exceptions inside individual test case runs are caught and logged inside the step metadata to prevent the entire benchmark suite from crashing.
* **Structured Output Guarantee**: Qualitative evaluation scores are strictly validated against Pydantic schemas, with retry loops handling parsing exceptions.

---

## 21. Limitations & Future Work
EvalForge is a self-hostable evaluation dashboard, not a commercial SaaS platform. Current limitations include:
* **BackgroundTasks queue**: Evaluation jobs run on FastAPI background thread workers rather than distributed task queues (e.g. Celery/Redis).
* **Single-user UX**: Visual layout is designed for local developers and contains no authentication or multi-tenant workspace separation.
* **Polling status checks**: Next.js dashboard polls run details endpoints for execution trace updates rather than using WebSockets or Server-Sent Events (SSE).

---

## 22. Project Status
**Completed & Stable**. The core evaluation framework, PostgreSQL connection pool, dataset and experiment engines, and UI dashboard are fully implemented, verified, and certified.

---

## 23. License
This project is licensed under the MIT License. See package details for information.
