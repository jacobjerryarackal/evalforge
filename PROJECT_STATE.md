# PROJECT_STATE — EvalForge

This document tracks the current sprint, active phase, completed milestones, engineering risks, and our architecture decision record (ADR) index.

---

## 1. Active State
- **Current Sprint**: **Sprint 1: Pluggable Core Engine & SUT Integration** (Completed)
- **Current Phase**: Phase 1 (Core Execution Backbone Setup)
- **Completion Percentage**: **40%** (Core backbone, providers, simulation services, SQLite repository, SUT, and E2E evaluation flow are complete)
- **Next Sprint**: **Sprint 2: Heuristic & Retrieval Metrics** (Scheduled)

---

## 2. Completed Work (Sprint 1)
- **SQLite Evaluation Repository**: Implemented [SqliteEvaluationRepository](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py) wrapping blocking `sqlite3` calls inside `asyncio.to_thread` for concurrent safety.
- **Pluggable LLM Adapters**: Created [GeminiProvider](file:///d:/AI/evalforge/src/adapters/llm/gemini.py), [OllamaProvider](file:///d:/AI/evalforge/src/adapters/llm/ollama.py), and [OpenRouterProvider](file:///d:/AI/evalforge/src/adapters/llm/openrouter.py) with mock fallback modes for offline developer setups.
- **Travel Simulation Layer**: Created deterministic catalog services under [services.py](file:///d:/AI/evalforge/src/infrastructure/travel_simulation/services.py) (Flights, Hotels, Weather, Currency, Attractions, Policy, and User Profiles).
- **Travel Agent SUT**: Built [TravelAgentSUT](file:///d:/AI/evalforge/src/infrastructure/mock_sut/travel_agent_sut.py) executing multi-turn reasoning loops, making tool calls, and generating trajectory data.
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
- **Sprint 2**: Heuristic constraint checks and Retrieval metrics (Context Recall/Precision).
- **Sprint 3**: Cognitive LLM-as-a-judge metrics (Faithfulness, Groundedness, Answer Correctness).
- **Sprint 4**: Safety evaluation metrics and golden dataset versioning / regression suites.
- **Sprint 5**: Rich CLI dashboard, and Jinja2 HTML report generator (Note: SQLite persistence implemented in Sprint 1).

---

## 4. Known Risks & Mitigations

| Risk Description | Severity | Mitigation Plan |
| :--- | :--- | :--- |
| **LLM Provider Rate Limiting (429 Errors)** | High | Bounded concurrency (Semaphore) restricts parallel cases. Sprint 1 LLM Adapters and Sprint 3 LLM Judges will add retry-backoff wrappers. |
| **Non-Deterministic LLM Judge Scores** | Medium | Structured Pydantic schema validation for JSON judge outputs, coupled with temperature=0.0 and failure retry loops. |
| **Concurrent DB Locks during parallel writes** | Medium | Implement serialized database writes or queue transactions in the SQLite Repository adapter (Sprint 5). |
| **Model Format Instability** | Medium | Implement format-checking schema validators to enforce expected JSON shapes and auto-retry on parsing error. |

---

## 5. ADR Index
We document architectural choices sequentially:
1. **[ADR-0001: Record Architecture Decisions](file:///d:/AI/evalforge/docs/adr/0001-record-architecture-decisions.md)**: Establishes ADR rules and sequential template.
2. **[ADR-0002: Tech Stack and Architectural Patterns](file:///d:/AI/evalforge/docs/adr/0002-tech-stack-and-architecture-patterns.md)**: Approves Python, Clean Architecture, Pydantic v2, and Repository pattern.
3. **[ADR-0003: Pluggable LLM Provider & Evaluation Metrics Specification](file:///d:/AI/evalforge/docs/adr/0003-pluggable-llm-provider-and-metrics-specification.md)**: Lays out the base evaluator structure and provider interfaces.
4. **[ADR-0004: SQLite Repository and Travel Agent SUT Design](file:///d:/AI/evalforge/docs/adr/0004-sqlite-repository-and-travel-agent-sut.md)**: Details SQLite schemas, thread wrapping, and SUT tool mocking.
