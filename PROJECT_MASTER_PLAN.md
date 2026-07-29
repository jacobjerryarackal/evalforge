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
EvalForge is developed in **5 compressed Engineering Sprints** designed to fit a 1-week timeline:

1. **Sprint 1: Pluggable Core Engine & Environments**: Implement concrete LLM adapters (Gemini, Ollama, OpenRouter) and a Mock Travel SUT agent wrapper exposing flight, hotel, and weather APIs.
2. **Sprint 2: Heuristic & Retrieval Metrics**: Implement deterministic checks (token usages, budgets, loop tracking, tool formats) and retrieval metrics (Context Precision, Context Recall).
3. **Sprint 3: Cognitive Metrics (LLM-as-a-Judge)**: Implement Groundedness, Faithfulness, and Answer Correctness metrics with Pydantic JSON schema judges.
4. **Sprint 4: Safety & Policy Auditing**: Implement safety evaluations (prompt injection, prompt leaks, PII) and versioned golden datasets/regression checks.
5. **Sprint 5: Persistence, Dashboard & HTML Reporting**: Implement SQLite db storage, a Rich CLI console dashboard, and static HTML reports exports.

---

## 4. Progress Tracking & Phase Completion
Progress is monitored sprint-by-sprint. A sprint is completed only when it clears the **Engineering Gate** defined in the Playbook.

| Sprint | Objective | Target Completion | Actual Completion | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sprint 0** | Engineering OS Initialization | Day 1 | 2026-07-29 | **Completed** |
| **Sprint 1** | Pluggable Engine & Environments | Day 2 | - | *Pending* |
| **Sprint 2** | Heuristic & Retrieval Metrics | Day 3 | - | *Pending* |
| **Sprint 3** | Cognitive Metrics (LLM Judge) | Day 4 | - | *Pending* |
| **Sprint 4** | Safety & Policy Auditing | Day 5 | - | *Pending* |
| **Sprint 5** | Persistence & Dashboard Reporting | Day 6 | - | *Pending* |

---

## 5. Dependencies
- **Runtime**: Python 3.11+
- **Validation**: Pydantic v2 (for robust parsing and type assertions)
- **APIs**: Httpx (async requests), Google Generative AI (Gemini SDK), OpenAI SDK (for OpenRouter compatibility)
- **Data & Reports**: Pandas/Polars (tabular logs), Jinja2 (HTML generation), Rich (CLI dashboards)
- **Quality Assurance**: Pytest (testing), Ruff (linting), Black (formatting), Mypy (type checking)

---

## 6. Definition of Done (DoD)
For any feature or sprint to be declared "Done" and merged, it must satisfy:
1. **Design Alignment**: Architectural design verified against clean layers; no domain logic leaks into adapters.
2. **Type Safety**: Mypy type check runs clean with zero issues.
3. **Code Quality**: Ruff check passes clean; Black formatting applied.
4. **Testing Coverage**: Unit tests written for all new domain models and use case orchestrators. Pytest suite passes successfully.
5. **Error Shielding**: Asynchronous execution handles SUT or evaluator failures gracefully without crashing.
6. **Documentation Updated**: Architecture charts, playbooks, and states updated to reflect changes.
