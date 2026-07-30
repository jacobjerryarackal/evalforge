# PROJECT_STATE — EvalForge

This document tracks the current sprint, active phase, completed milestones, engineering risks, and our architecture decision record (ADR) index.

---

## 1. Active State
- **Current Sprint**: **Sprint 5: Platform & Productization** (Completed)
- **Current Phase**: Phase 5 (REST APIs, Next.js Dashboard, Reporting, Docker)
- **Completion Percentage**: **100%** (FastAPI backend, Next.js dashboard workspace, markdown reports, structured logging, Docker deployment assets, and CI workflows completed and verified)
- **Next Sprint**: None (Framework & Platform is production-grade)

---

## 2. Completed Work (Sprint 5)
- **FastAPI Backend REST API**: Implemented endpoints in [app.py](file:///d:/AI/evalforge/src/adapters/api/app.py) for datasets cataloging, experiment comparing, async run execution via background task workers, run details, and health check.
- **Next.js Dashboard**: Implemented a visual UI workspace in [page.tsx](file:///d:/AI/evalforge/dashboard/src/app/page.tsx) with state tabs, run creation form inputs, comparative delta tables, and run trajectory inspect traces.
- **Markdown Reporting**: Created [markdown.py](file:///d:/AI/evalforge/src/use_cases/reporting/markdown.py) to compile rich markdown reports summarizing scores, metrics, cost, tokens, and trajectory step lists.
- **Observability structured logs**: Created [formatter.py](file:///d:/AI/evalforge/src/infrastructure/logging/formatter.py) implementing a `JSONFormatter`, and updated `BenchmarkRunner` to emit execution parameters in logs.
- **Deployment & CI assets**: Created backend and frontend [Dockerfile](file:///d:/AI/evalforge/Dockerfile), root [docker-compose.yml](file:///d:/AI/evalforge/docker-compose.yml), and GitHub Action workflow [ci.yml](file:///d:/AI/evalforge/.github/workflows/ci.yml).
- **Verification**: Created 4 integration tests (totaling 68 passed tests). Mypy, Ruff, and Black checks pass cleanly.

## Completed Work (Sprint 4)
- **LLM Judge Engine**: Built [LLMJudgeEngine](file:///d:/AI/evalforge/src/use_cases/judges/engine.py) implementing Pydantic structured output parsing, text fallback manual JSON block extraction, rate limit retry loops with exponential backoff, and confidence validation.
- **Base Judge Interface**: Built [BaseLLMJudge](file:///d:/AI/evalforge/src/use_cases/judges/base.py) representing the core base class for qualitative LLM Judges, inheriting from `BaseEvaluator` for seamless execution.
- **Judge Prompt Templates**: Built [JudgePromptTemplate](file:///d:/AI/evalforge/src/use_cases/judges/templates.py) separating prompts and scoring rubrics from Python logic, with default templates for cognitive assessments.
- **Cognitive Judges**: Implemented `FaithfulnessJudge`, `GroundednessJudge`, `AnswerCorrectnessJudge`, and `HallucinationJudge`.
- **Judge Registry**: Implemented [JudgeRegistry](file:///d:/AI/evalforge/src/use_cases/judges/registry.py) managing registration and duplicate validation of LLM Judges.
- **Verification**: Created 11 new tests (totaling 64 passed tests). Ruff linter, Black formatting, and Mypy type checks are completely clean.


## Completed Work (Sprint 3)
- **Dataset Registry**: Built [DatasetRegistry](file:///d:/AI/evalforge/src/use_cases/datasets/registry.py) which handles dataset registration, compound key uniqueness validation on `(dataset_id, version)`, and discovery.
- **Dataset Loader**: Built [DatasetLoader](file:///d:/AI/evalforge/src/use_cases/datasets/loader.py) with full support for JSON and line-by-line JSONL datasets, containing advanced diagnostic line-numbered syntax reporting.
- **Dataset Validator**: Built [DatasetValidator](file:///d:/AI/evalforge/src/use_cases/datasets/validator.py) which enforces SemVer version strings, required fields, unique case IDs, and validates type constraints.
- **Benchmark Configuration**: Created [BenchmarkConfig](file:///d:/AI/evalforge/src/domain/entities/benchmark_config.py) and integrated it into the runner, adding SUT exponential backoff retries and metrics execution filters.
- **Experiment Engine**: Implemented [Experiment](file:///d:/AI/evalforge/src/domain/entities/experiment.py) domain model and [ExperimentEngine](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py) to save experiments, compute performance deltas relative to baseline runs, and compile rich markdown summary reports.
- **Verification**: Created 12 new tests (totaling 53 passed tests). Ruff linter, Black formatting, and Mypy type-checking are completely clean.

## Completed Work (Sprint 2B)
- **Metric Registry**: Built [MetricRegistry](file:///d:/AI/evalforge/src/use_cases/metrics/registry.py) which handles evaluator registration, duplicate checking, discovery, and retrieval by name.
- **Aggregated Statistics**: Created [AggregationEngine](file:///d:/AI/evalforge/src/use_cases/metrics/aggregation.py) which separates scoring logic from `EvaluationRun` data models, facilitating custom averages/totals computations.
- **Refactored Runner**: Decoupled [BenchmarkRunner](file:///d:/AI/evalforge/src/use_cases/runners/benchmark_runner.py) using the Registry pattern; it no longer imports or directly instantiates concrete evaluators.
- **Concrete Evaluators**: Implemented 6 deterministic evaluators under [evaluators.py](file:///d:/AI/evalforge/src/use_cases/metrics/evaluators.py): `Latency`, `TokenUsage`, `Cost`, `ToolCalling`, `ContextPrecision`, and `ContextRecall`.
- **Verification**: Created 12 new tests (totaling 41 passed tests). Ruff linter, Black formatting, and Mypy type checks are completely clean.

## Completed Work (Sprint 2A)
- **Decoupled Architecture**: Refactored package boundaries to make the core evaluation engine entirely domain-independent.
- **Reference Implementation**: Created `examples/travel_agent/` housing the Travel Agent SUT and travel catalog simulation services.
- **Imports Restructuring**: Cleaned all import footprints in the core framework (`src/`) to ensure absolutely zero dependency on travel business concepts.
- **Test Isolation**: Updated and verified all unit and E2E tests, ensuring they remain 100% green with zero modifications to runtime agent behaviors.

## Completed Work (Sprint 1)
- **SQLite Evaluation Repository**: Implemented [SqliteEvaluationRepository](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py) wrapping blocking `sqlite3` calls inside `asyncio.to_thread` for concurrent safety.
- **Pluggable LLM Adapters**: Created [GeminiProvider](file:///d:/AI/evalforge/src/adapters/llm/gemini.py), [OllamaProvider](file:///d:/AI/evalforge/src/adapters/llm/ollama.py), and [OpenRouterProvider](file:///d:/AI/evalforge/src/adapters/llm/openrouter.py) with mock fallback modes for offline developer setups.
- **E2E Integration**: Connected golden datasets, SUT execution, trajectories, evaluators, and SQLite database storage in [test_e2e_evaluation.py](file:///d:/AI/evalforge/tests/integration/test_e2e_evaluation.py).
- **Verification**: Created 19 new tests, achieving 29/29 passing tests. Codebase is 100% Black-formatted, Ruff-compliant, and Mypy type-safe.

## Completed Work (Sprint 0)
- **Directory Spine**: Created clean architecture folders under `src/` and `tests/`.
- **Environment & Packing**: Established `pyproject.toml`, `requirements.txt`, and `.gitignore`. Activated virtual environment (`.venv`) and installed Pydantic, Pandas, Pytest, Black, Ruff, and Mypy.
- **Domain Value Objects & Entities**: Implemented immutable metrics (`TokenUsage`, `Cost`, `Latency`) and entities (`Step`, `ToolCall`, `Trajectory`, `GoldenTestCase`, `GoldenDataset`, `MetricResult`, `TestCaseEvaluation`, `EvaluationRun`).
- **Core Interfaces**: Defined boundaries for `AgentSUT`, `LLMProvider`, `EvaluationRepository`, and `BaseEvaluator`.
- **Use Cases**: Implemented `BenchmarkRunner` supporting bounded concurrency via Semaphore and per-case fault shielding.
- **Adapters**: Created `InMemoryEvaluationRepository` with copy-isolation.
- **Operating System Docs**: Created `PROJECT_MASTER_PLAN.md`, `ENGINEERING_PLAYBOOK.md`, `PROJECT_STATE.md`, and `ROADMAP.md`.
- **Verification**: 10 unit tests passing successfully. Ruff linter and Mypy type-checking clean.

---

## 3. Pending Work (Roadmap)
- **All Sprints Completed**: Core framework, dataset and experiment engines, LLM cognitive judges, REST APIs, Next.js dashboard, structured JSON logging, and Docker compose assets are fully implemented.

---

## 4. Known Risks & Mitigations

| Risk Description | Severity | Mitigation Plan |
| :--- | :--- | :--- |
| **LLM Provider Rate Limiting (429 Errors)** | Low (Mitigated) | Bounded concurrency (Semaphore) restricts parallel cases. LLM Adapters and LLM Judges utilize exponential backoff retry loops. |
| **Non-Deterministic LLM Judge Scores** | Low (Mitigated) | Structured Pydantic schema validation for JSON judge outputs, coupled with temperature=0.0 and failure retry loops. |
| **Concurrent DB Locks during parallel writes** | Low (Mitigated) | Thread-safe database writes wrapped in `asyncio.to_thread` via the SQLite Repository adapter. |
| **Model Format Instability** | Low (Mitigated) | Implement format-checking schema validators to enforce expected JSON shapes and auto-retry on parsing error. |

---

## 5. ADR Index
We document architectural choices sequentially:
1. **[ADR-0001: Record Architecture Decisions](file:///d:/AI/evalforge/docs/adr/0001-record-architecture-decisions.md)**: Establishes ADR rules and sequential template.
2. **[ADR-0002: Tech Stack and Architectural Patterns](file:///d:/AI/evalforge/docs/adr/0002-tech-stack-and-architecture-patterns.md)**: Approves Python, Clean Architecture, Pydantic v2, and Repository pattern.
3. **[ADR-0003: Pluggable LLM Provider & Evaluation Metrics Specification](file:///d:/AI/evalforge/docs/adr/0003-pluggable-llm-provider-and-metrics-specification.md)**: Lays out the base evaluator structure and provider interfaces.
4. **[ADR-0004: SQLite Repository and Travel Agent SUT Design](file:///d:/AI/evalforge/docs/adr/0004-sqlite-repository-and-travel-agent-sut.md)**: Details SQLite schemas, thread wrapping, and SUT tool mocking.
5. **[ADR-0005: Metrics Engine Registry and Aggregation Design](file:///d:/AI/evalforge/docs/adr/0005-metrics-engine-registry-and-aggregation.md)**: Details registry pattern, aggregation engine, and default metrics.
6. **[ADR-0006: Platform & REST API Specification](file:///d:/AI/evalforge/docs/adr/0006-platform-and-rest-api-specification.md)**: Details REST endpoints, Next.js architecture, Docker, and logging formatters.


