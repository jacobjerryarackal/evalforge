# EvalForge — Release Candidate (RC1) Verification Checklist

This checklist provides the steps required to verify a Release Candidate (RC) and prepare EvalForge for a production `v1.0.0` release.

---

## 1. Local Environment Setup

- [ ] **Python Setup**: Verify Python version is 3.11+.
  ```bash
  python --version
  ```
- [ ] **Virtual Environment**: Create and activate a clean `.venv`:
  ```bash
  python -m venv .venv
  # Windows:
  .venv\Scripts\activate
  # macOS/Linux:
  source .venv/bin/activate
  ```
- [ ] **Python Packages**: Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- [ ] **Node Setup**: Verify Node version is 18+.
  ```bash
  node --version
  ```
- [ ] **Next.js Project Setup**: Install frontend npm packages:
  ```bash
  cd frontend
  npm install
  cd ..
  ```
- [ ] **Environment Configuration**: Create `.env` files in root and `frontend/` folders:
  - **Root `.env`**:
    ```env
    GEMINI_API_KEY=your-gemini-key
    OLLAMA_API_BASE=http://localhost:11434
    OPENROUTER_API_KEY=your-openrouter-key
    DATABASE_URL=sqlite:///evalforge_platform.db
    ```
  - **Frontend `.env`**:
    ```env
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```

---

## 2. CI Verification (Static Analysis & Tests)

Run the static verification suite in the root directory:
- [ ] **Code Formatting (Black)**: Verify Black formatting rules.
  ```bash
  .venv\Scripts\python -m black --check src tests examples
  ```
- [ ] **Lint Verification (Ruff)**: Verify code quality and import patterns.
  ```bash
  .venv\Scripts\python -m ruff check src tests examples
  ```
- [ ] **Static Type Analysis (Mypy)**: Verify type safety constraints.
  ```bash
  .venv\Scripts\python -m mypy src tests examples
  ```
- [ ] **Unit & Integration Tests (Pytest)**: Execute the full 68-test suite.
  ```bash
  .venv\Scripts\python -m pytest
  ```
  *(Verify that 68 tests pass with 0 failures)*

---

## 3. Backend Service Verification

- [ ] **Start FastAPI server**:
  ```bash
  .venv\Scripts\python -m uvicorn src.adapters.api.app:app --host 127.0.0.1 --port 8000
  ```
- [ ] **API Docs**: Access Swagger UI at http://127.0.0.1:8000/docs. Verify all schemas load correctly.
- [ ] **Health Endpoint**: Curl health endpoint:
  ```bash
  curl http://127.0.0.1:8000/health
  ```
  *(Expected response: `{"status":"healthy",...}`)*

---

## 4. Frontend Service Verification

- [ ] **Next.js Production Build**: Compile and build static Next.js pages:
  ```bash
  cd frontend
  npm run build
  cd ..
  ```
  *(Verify "Compiled successfully" and static pages are generated without errors)*
- [ ] **Start Next.js dev server**:
  ```bash
  cd frontend
  npm run dev
  ```
- [ ] **Dashboard Access**: Load http://localhost:3000 in your browser.

---

## 5. Docker Compose Verification

- [ ] **Docker Service Build**: Verify multi-container Docker compilation.
  ```bash
  docker-compose build
  ```
- [ ] **Docker Launch**: Run services in the background:
  ```bash
  docker-compose up -d
  ```
- [ ] **Networking verification**: Confirm that http://localhost:3000 successfully reaches backend service on http://localhost:8000 inside containers.
- [ ] **Docker Stop**: Stop and prune compose resources:
  ```bash
  docker-compose down
  ```

---

## 6. Manual QA Checklist (End-to-End Workflow)

Follow these steps to manually verify the platform workspace:
1. **Connection Badge**: Load http://localhost:3000. Verify the top-right indicator shows **Connected** in green.
2. **Datasets Hub**:
   - Navigate to the **Datasets** tab.
   - Fill the **Register Golden Dataset** form:
     - Dataset ID: `ds-test-travel`
     - Dataset Name: `Travel Test Suite`
     - Version: `1.0.0`
     - Input Query: `Book flight JFK to LAX on 2026-08-01 for user U101`
     - Expected Output: `Flight UA100`
   - Click **Register Dataset**.
   - Verify the dataset appears in the **Registered Datasets Catalog** on the right.
3. **Experiments Sweep**:
   - Navigate to the **Experiments** tab.
   - Create an experiment sweep:
     - Experiment ID: `exp-test-sweep`
     - Experiment Name: `Flight Spend Sweep`
     - Description: `Testing spend limits`
   - Click **Create Experiment**.
   - Verify the sweep is registered in the catalog.
4. **Trigger Benchmark**:
   - Navigate to the **Overview** tab.
   - Locate the **Trigger Async Benchmark** form.
   - Select Dataset ID: `ds-test-travel`
   - Select Dataset Version: `1.0.0`
   - Associate Experiment: `exp-test-sweep`
   - Click **Launch Execution Job**.
   - Verify the green status notification appears: `Started successfully! Run ID: run-...`.
5. **Trace Inspection**:
   - Navigate to the **Run History** tab.
   - Find the newly triggered run and click **Inspect Trace**.
   - Verify the **Test Case Traces** panel loads, rendering:
     - Case ID: `case-1` (Passed/Failed status)
     - Executed Query details.
     - Extracted execution metrics (Faithfulness, Groundedness, Latency, Cost).
   - Verify the **Run Report (Markdown)** details compile successfully.
6. **Comparison Report**:
   - Navigate to the **Experiments** tab.
   - Click the registered experiment `exp-test-sweep`.
   - Verify the comparison report compiles, displaying the registered run details and markdown analysis.

---

## 7. Known Limitations & Mitigations

- **SQLite Locking**: SQLite is a single-user serverless database. Concurrent writes from multiple parallel runs can trigger `database is locked` exceptions.
  - *Mitigation*: Bounded async thread delegation handles repository access sequentially via `asyncio.to_thread`.
- **LLM Token Costs**: Running large dataset sweeps can incur significant API costs and hit rate limits.
  - *Mitigation*: The `BenchmarkConfig` enforces concurrent limits (semaphore boundaries) and retry policies with exponential backoff handlers.
