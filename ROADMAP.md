# ROADMAP — EvalForge 1-Week Optimized Timeline

This document maps out our compressed 5-sprint roadmap to build and verify **EvalForge** in 6 engineering days while preserving production-grade engineering quality.

```
 Day 1-2: Pluggable Core ──> Day 3: Heuristics/Retrieval ──> Day 4: Cognitive Metrics
                                                                       │
 Day 6: Storage/Dashboard <── Day 5: Safety & Regression <─────────────┘
```

---

## Sprint 1: Pluggable Core Engine & SUT Integration (Days 1–2)
- **Goal**: Implement concrete LLM adapters and a mock Travel Agent System Under Test (SUT) with access to mock flight, hotel, and weather APIs. This establishes the base operational environment.
- **Key Deliverables**:
  - **LLM Adapters** in `src/adapters/llm/`:
    - `GeminiProvider`: Native wrapper using `google-generativeai`.
    - `OpenRouterProvider`: Compatibility layer for open-source model providers using `openai` API patterns.
    - `OllamaProvider`: Connects to local offline endpoints (e.g., `localhost:11434`) for local test sweeps.
  - **Mock Travel SUT** in `src/infrastructure/mock_sut/`:
    - Concrete implementation of the `AgentSUT` interface.
    - Mock Tool APIs: `flight_search`, `hotel_availability`, and `weather_lookup` (intentionally seeded with constraint boundary scenarios, dates, and bug-prone responses).
- **Verification Gate**:
  - Run integration tests showing the runner executing a mock test case query against `TravelAgentSUT`, executing tool calls, and capturing a complete multi-turn `Trajectory` successfully.

---

## Sprint 2: Heuristic & Retrieval Metrics (Day 3)
- **Goal**: Implement deterministic metric checkers (budgets, execution boundaries) and context retrieval metrics to check validation indexes.
- **Key Deliverables**:
  - **Heuristic Evaluators** in `src/use_cases/evaluators/`:
    - `TokenBudgetEvaluator`: Flags runs exceeding token counts.
    - `CostConstraintEvaluator`: Flags runs exceeding price thresholds.
    - `ToolCallValidator`: Audits argument syntax, invalid formats, and checks for "infinite tool call loops".
  - **Retrieval Evaluators** in `src/use_cases/evaluators/`:
    - `ContextPrecisionEvaluator`: Measures how relevant retrieved context is compared to ground truth.
    - `ContextRecallEvaluator`: Measures if all necessary ground truth context was retrieved.
- **Verification Gate**:
  - Pytest unit suite in `tests/unit/test_retrieval_metrics.py` asserting correct precision and recall scores against mocked datasets.

---

## Sprint 3: Dataset & Experiment Engine (Day 4)
- **Goal**: Make datasets, benchmark configurations, and experiments first-class entities with version control, loading, and structured comparison.
- **Key Deliverables**:
  - **Dataset Engine** in `src/use_cases/datasets/`:
    - `DatasetRegistry`, `DatasetValidator`, `DatasetLoader`.
  - **Benchmark Configuration**:
    - `BenchmarkConfig`, `RetryPolicy` Pydantic models.
  - **Experiment Engine** in `src/use_cases/experiments/`:
    - `Experiment` domain model, `ExperimentEngine`, `ExperimentComparer` and `ExperimentSummaryGenerator`.
- **Verification Gate**:
  - Run unit tests verifying dataset registry uniqueness, JSON/JSONL loading and parsing errors, validator constraints checking, SUT retry exponential backoffs, and experiment comparisons.

---

## Sprint 4: LLM Judge Engine (Day 5)
- **Goal**: Build a reusable execution engine, registries, templates, and cognitive LLM Judges that grade qualitative agent responses.
- **Key Deliverables**:
  - **Base Judge Interface** in `src/use_cases/judges/base.py`:
    - `BaseLLMJudge` inheriting from `BaseEvaluator`.
  - **LLM Judge Engine** in `src/use_cases/judges/engine.py`:
    - `LLMJudgeEngine` executing prompt templates, parsing schemas, retrying transient failures, and validating confidence.
  - **Templates & Registry** in `src/use_cases/judges/`:
    - `JudgePromptTemplate`, `JudgeRegistry`, and default cognitive templates.
  - **Initial Judges**:
    - `FaithfulnessJudge`, `GroundednessJudge`, `AnswerCorrectnessJudge`, `HallucinationJudge`.
- **Verification Gate**:
  - Run unit and integration tests verifying registry duplicates, templates rendering, engine fallback json parsing, retries, and all four judges under different outcomes.

---

## Sprint 5: Database Persistence & Dashboard Reporting (Day 6)
- **Goal**: Provide physical database storage (SQLite) and build user interfaces (console dashboard and HTML reports) to make EvalForge a complete, visual platform.
- **Key Deliverables**:
  - **Database Repository** in `src/adapters/repositories/sqlite_repository.py`:
    - Concrete SQLite implementation of `EvaluationRepository` mapping entities to SQL tables.
  - **Console Dashboard** in `src/adapters/cli/`:
    - An interactive, styled CLI display showing real-time run metrics, token costs, and average metrics using `rich`.
  - **HTML Report Generator** in `src/adapters/cli/`:
    - Static HTML report compiler using Jinja2 templates, rendering graphs, charts, and detailed trajectories.
- **Verification Gate**:
  - End-to-end integration test executing a benchmark run on a local dataset, saving the results in SQLite, and generating a validated HTML report file.
