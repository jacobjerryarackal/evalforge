# PROJECT_STATE — EvalForge

This document tracks the current sprint, active phase, completed milestones, engineering risks, and our architecture decision record (ADR) index.

---

## 1. Active State
- **Current Sprint**: **Sprint 0: Engineering Operating System Initialization** (Completed)
- **Current Phase**: Phase 0 (Foundations & Requirements Setup)
- **Completion Percentage**: **20%** (Project spine, environment, core runner engine, domain entities, and OS documents are complete)
- **Next Sprint**: **Sprint 1: Pluggable Core Engine & SUT Integration** (Scheduled)

---

## 2. Completed Work (Sprint 0)
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
- **Sprint 1**: Pluggable LLM Providers (Gemini, Ollama, OpenRouter) and Mock Travel Agent SUT with flight/hotel tools.
- **Sprint 2**: Heuristic constraint checks and Retrieval metrics (Context Recall/Precision).
- **Sprint 3**: Cognitive LLM-as-a-judge metrics (Faithfulness, Groundedness, Answer Correctness).
- **Sprint 4**: Safety evaluation metrics and golden dataset versioning / regression suites.
- **Sprint 5**: Concrete SQLite repository persistence, Rich CLI dashboard, and Jinja2 HTML report generator.

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
