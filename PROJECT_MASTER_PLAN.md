# PROJECT_MASTER_PLAN — EvalForge

This document establishes the strategic direction, architectural bounds, roadmap, progress tracking, and quality standards for **EvalForge**—our production-grade, model-agnostic AI Agent Evaluation Platform.

---

## 1. Vision
**EvalForge** is designed to benchmark, audit, and observe AI agents operating under complex, multi-turn constraint environments (e.g., travel reservation assistants, customer support agents). It provides engineers with a unified, provider-independent testing harness to measure token costs, latencies, retrieval precision, constraint satisfaction, cognitive hallucinations, and safety compliance across pluggable LLM backends (Gemini, Ollama, OpenRouter).

---

## 2. Architecture Summary
EvalForge strictly adheres to **Clean Architecture** and **Domain-Driven Design (DDD)** principles to decouple core evaluation rules from external providers and tools.

```
       Infrastructure Layer (SQLite repositories, raw HTTP clients, mock GDS toolkits)
                                         │
                                         ▼
       Adapter Layer (Gemini SDK, OpenRouter REST client, SQLite DB adapter, Rich Console CLI)
                                         │
                                         ▼
       Use Case Layer (BenchmarkRunner orchestrator, Metric evaluators)
                                         │
                                         ▼
       Domain Layer (Entities: Step, Trajectory, GoldenTestCase; Value Objects: Cost, Latency)
```

- **Domain Layer (`src/domain/`)**: Pure entities, value objects, and abstract interface contracts. No dependencies on external frameworks or APIs.
- **Use Case Layer (`src/use_cases/`)**: Application services coordinating evaluation loops, statistical summaries, and metric calculations.
- **Adapter Layer (`src/adapters/`)**: Concrete wrappers implementing domain interfaces (e.g., LLM providers, database storage engines, console CLI outputs).
- **Infrastructure Layer (`src/infrastructure/`)**: Low-level database connections, mock System Under Test (SUT) APIs, and config setups.

---

## 3. Compressed Roadmap Overview
EvalForge is developed in **6 compressed Engineering Sprints** designed to fit a 1-week timeline (Days 1–6):

| Sprint | Objective | Duration | Target Date | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sprint 0** | Engineering OS Initialization | Day 1 | Day 1 | **Completed** |
| **Sprint 1** | Pluggable Core Engine & SUT Integration | Days 1–2 | Day 2 | **Completed** |
| **Sprint 2** | Heuristic & Retrieval Metrics | Day 3 | Day 3 | **Completed** |
| **Sprint 3** | Dataset & Experiment Engine | Day 4 | Day 4 | **Completed** |
| **Sprint 4** | Cognitive Metrics (LLM Judge) | Day 5 | Day 5 | *Pending* |
| **Sprint 5** | Database Persistence & Dashboard Reporting | Day 6 | Day 6 | *Pending* |

---

## 4. Sprint Specifications

### Sprint 0: Engineering OS Initialization
- **Goal**: Establish development environment, folder structure, pure domain models, core interfaces, and concurrent evaluation runner.
- **Deliverables**:
  - Virtual environment configuration, `pyproject.toml`, and `.gitignore`.
  - Pure domain value objects: [TokenUsage](file:///d:/AI/evalforge/src/domain/value_objects/__init__.py), `Cost`, `Latency`.
  - Domain entities: `Step`, `Trajectory`, `GoldenTestCase`, `GoldenDataset`, `EvaluationRun`.
  - Repository interfaces & concurrent [BenchmarkRunner](file:///d:/AI/evalforge/src/use_cases/runners/benchmark_runner.py) with bounded concurrency semaphores.
- **Definition of Done (DoD)**:
  - 100% of unit tests pass.
  - Ruff and black formats check out clean. Mypy runs with zero type errors.
  - Engineering operating system documents are initialized.
- **Verification**:
  - Run `pytest` on `tests/unit/test_domain_models.py` and `tests/unit/test_benchmark_runner.py`.
- **Interview Topics**:
  - Clean Architecture boundaries and DIP benefits.
  - Mutability vs. Immutability of Domain Value Objects.
  - Implementing thread-safe / task-safe bounded concurrency with asyncio Semaphores.

### Sprint 1: Pluggable Core Engine & SUT Integration
- **Goal**: Implement concrete LLM adapters and a mock Travel Agent SUT with travel tool APIs.
- **Deliverables**:
  - `GeminiProvider`, `OpenRouterProvider`, and `OllamaProvider` in `src/adapters/llm/`.
  - `TravelAgentSUT` mock agent implementing the `AgentSUT` interface.
  - Mock Tool APIs: flight search, hotel availability, weather lookup.
- **Definition of Done (DoD)**:
  - All providers implement [LLMProvider](file:///d:/AI/evalforge/src/domain/interfaces/llm_provider.py) cleanly.
  - TravelAgentSUT correctly calls APIs and handles tools.
  - Trajectory captures step outputs and costs.
- **Verification**:
  - Integration tests running mock queries against `TravelAgentSUT` and capturing a multi-turn trajectory.
- **Interview Topics**:
  - Integration of Gemini and OpenAI SDKs.
  - Mocking third-party tooling APIs.
  - Managing multi-turn context trajectories and handling API rate limits/timeouts.

### Sprint 2: Heuristic & Retrieval Metrics
- **Goal**: Implement deterministic metric checkers and context retrieval precision/recall metrics.
- **Deliverables**:
  - Heuristics: `TokenBudgetEvaluator`, `CostConstraintEvaluator`, `ToolCallValidator` (loop checker).
  - Retrieval: `ContextPrecisionEvaluator`, `ContextRecallEvaluator` under `src/use_cases/evaluators/`.
- **Definition of Done (DoD)**:
  - Metric evaluators extend `BaseEvaluator` contract.
  - Infinite tool-call loops are successfully detected and aborted.
  - Precision/recall metrics calculations verify correctly against mock indexes.
- **Verification**:
  - Unit tests in `tests/unit/test_retrieval_metrics.py` asserting metric outputs.
- **Interview Topics**:
  - Precision and Recall in information retrieval.
  - Implementing execution boundary guards for agent safety.
  - Profiling token usages and calculating live API costs.

### Sprint 3: Dataset & Experiment Engine
- **Goal**: Make datasets, benchmark configurations, and experiments first-class entities with version control, loading, and structured comparison.
- **Deliverables**:
  - `DatasetRegistry`, `DatasetValidator`, `DatasetLoader` in `src/use_cases/datasets/`.
  - `BenchmarkConfig`, `RetryPolicy` Pydantic models in `src/domain/entities/`.
  - `Experiment` domain model and `ExperimentEngine` in `src/use_cases/experiments/`.
  - Persistence implementations for experiments in SQLite and InMemory repositories.
- **Definition of Done (DoD)**:
  - JSON and JSONL datasets parse and validate cleanly.
  - SUT executions retry with exponential backoff on transient errors.
  - Experiment runs are stored, retrieved, and summarized.
- **Verification**:
  - Unit tests verifying Registry, Loader, Validator, Config retries, and Experiment comparisons.
- **Interview Topics**:
  - Rationale for versioning evaluation datasets.
  - Benefits of decoupling BenchmarkConfig from runner orchestration.
  - Treating experiments as first-class objects to track deltas over time.

### Sprint 4: Cognitive Metrics (LLM-as-a-Judge)
- **Goal**: Build advanced cognitive metrics using a secondary model with structured outputs and error handling.
- **Deliverables**:
  - Cognitive Evaluators: `FaithfulnessEvaluator`, `GroundednessEvaluator`, `AnswerCorrectnessEvaluator`.
  - Structured judge wrapper enforcing Pydantic JSON outputs from LLM adapters with auto-retry loops on parse errors.
- **Definition of Done (DoD)**:
  - Secondary judge queries models using strict JSON schemas.
  - Parse failures are caught and retried cleanly.
- **Verification**:
  - Integration tests validating LLM judge outputs against pre-defined hallucinated responses.
- **Interview Topics**:
  - Design of LLM-as-a-judge pipelines.
  - Resolving non-determinism in model grading.
  - Cost/latency trade-offs of running judge evaluations in parallel.


### Sprint 5: Database Persistence & Dashboard Reporting
- **Goal**: Implement database storage and terminal/HTML visualization displays.
- **Deliverables**:
  - SQLite database schema & repository implementation (`sqlite_repository.py`).
  - Rich CLI dashboard displaying live execution status and metrics.
  - Jinja2 HTML report generator to compile static reports.
- **Definition of Done (DoD)**:
  - Evaluation results, costs, and trajectories persist fully in SQLite.
  - HTML reports compile and open successfully in standard web browsers.
- **Verification**:
  - End-to-end integration test creating a run, storing results in SQLite, and generating a report file.
- **Interview Topics**:
  - SQLite write locks mitigation under concurrent workloads.
  - Building high-fidelity CLI dashboards.
  - Designing static HTML report files for team alignment.

---

## 5. Definition of Done (DoD) - Global Gate
For any feature or sprint to be declared "Done" and merged, it must satisfy:
1. **Design Alignment**: Architectural design verified against clean layers; no domain logic leaks into adapters.
2. **Type Safety**: Mypy type check runs clean with zero issues.
3. **Code Quality**: Ruff check passes clean; Black formatting applied.
4. **Testing Coverage**: Unit tests written for all new domain models and use case orchestrators. Pytest suite passes successfully.
5. **Error Shielding**: Asynchronous execution handles SUT or evaluator failures gracefully without crashing.
6. **Documentation Updated**: Architecture charts, playbooks, and states updated to reflect changes.
