# PROJECT_KNOWLEDGE — EvalForge Long-Term Engineering Memory

This file serves as the permanent engineering memory for the **EvalForge** project. It documents the core vision, architectural rationale, key decision histories, provider strategies, evaluation concepts, implementation assumptions, and known limitations.

---

## 1. Project Vision
**EvalForge** is a production-grade, model-agnostic AI Agent Evaluation Framework. Inspired by modern agent observation needs (e.g., Booking.com 2026), it is designed to benchmark, audit, and observe AI agents running under complex, multi-turn constraint environments (such as a travel booking assistant).

The system allows engineers to:
1. Run standardized datasets (Golden Cases) against an agent.
2. Track the agent's interaction steps (Trajectories).
3. Evaluate the trajectories using deterministic heuristics, context retrieval checks, cognitive LLM-as-a-judge scorers, and safety policy audits.
4. Visualize performance (cost, latency, tokens, correctness) in real time.

---

## 2. Architecture Summary
EvalForge strictly adheres to **Clean Architecture** and **Domain-Driven Design (DDD)** principles.

```
       Infrastructure Layer (SQLite repositories, raw HTTP clients, mock SUT APIs)
                                         │
                                         ▼
       Adapter Layer (Gemini SDK, OpenRouter API, SQLite DB adapter, Rich Console CLI)
                                         │
                                         ▼
       Use Case Layer (BenchmarkRunner orchestrator, Metric evaluators)
                                         │
                                         ▼
       Domain Layer (Entities: Step, Trajectory, GoldenTestCase; Value Objects: Cost, Latency)
```

- **Domain (`src/domain/`)**: Houses core, pure business models (e.g., [EvaluationRun](file:///d:/AI/evalforge/src/domain/entities/evaluation_run.py) or [Trajectory](file:///d:/AI/evalforge/src/domain/entities/trajectory.py)). No dependencies on external frameworks or databases. Defines boundaries via abstract interfaces (e.g., [LLMProvider](file:///d:/AI/evalforge/src/domain/interfaces/llm_provider.py)).
- **Use Cases (`src/use_cases/`)**: Contains application rules (e.g., [BenchmarkRunner](file:///d:/AI/evalforge/src/use_cases/runners/benchmark_runner.py) and various metric evaluators).
- **Adapters (`src/adapters/`)**: Bridges interfaces with concrete technologies, such as LLM client adapters (`GeminiProvider`, `OllamaProvider`, `OpenRouterProvider`) and database repositories ([SqliteEvaluationRepository](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py)).
- **Infrastructure (`src/infrastructure/`)**: Standard environment loaders and database setup components.
- **Examples (`examples/`)**: Houses reference implementations of SUTs and catalog simulations, such as the [TravelAgentSUT](file:///d:/AI/evalforge/examples/travel_agent/travel_agent_sut.py) and [services.py](file:///d:/AI/evalforge/examples/travel_agent/services.py), illustrating how external agents plug into the framework's interfaces.

---

## 3. Important Decisions (ADR Summary)
Architectural choices are documented formally via ADRs under `docs/adr/`.
1. **[ADR-0001: Record Architecture Decisions](file:///d:/AI/evalforge/docs/adr/0001-record-architecture-decisions.md)**: Establish standardized markdown ADR template for traceability.
2. **[ADR-0002: Tech Stack and Architectural Patterns](file:///d:/AI/evalforge/docs/adr/0002-tech-stack-and-architecture-patterns.md)**: Selected Python 3.11+, Pydantic v2 (for strict data parsing/validation), and the Repository pattern to isolate data storage.
3. **[ADR-0003: Pluggable LLM Provider & Evaluation Metrics Specification](file:///d:/AI/evalforge/docs/adr/0003-pluggable-llm-provider-and-metrics-specification.md)**: Designed pluggable evaluation abstractions, segregating heuristics, context retrieval, and cognitive scorers.

---

## 4. Interview Notes (Technical Mentorship)
This section acts as a handbook for engineering reviews and technical interviews:
- **The Why**: Clean architecture was selected because LLM providers and agent configurations change rapidly. Decoupling ensures we can swap from Gemini to Ollama (offline) or change our database from JSON files to PostgreSQL without touching core scoring logic.
- **The Alternatives**: We rejected global states and inline client initialization (e.g., calling `google.generativeai` directly inside the scoring code). While fast to write, it makes testing impossible, couples the framework to one API, and hides API costs.
- **Production Considerations**: Latency is the main blocker for LLM-as-a-judge evaluators. In production, evaluators must run asynchronously with bounded concurrency. Bounded semaphores prevent exceeding rate limits (429s).
- **Beginner Mistakes**:
  - *Hardcoding API configurations*: Resolved via constructor-injected configurations.
  - *Empty Try-Except blocks*: Avoided; all exceptions must log failures and yield structured `EvaluationRun` error summaries.
- **Real-World Analogy**: Major reservation systems (like Booking.com) test their agents by playing simulated flight bookings against sandboxed APIs to verify that agents don't buy tickets exceeding customer budgets.

---

## 5. Provider Strategy
EvalForge supports a pluggable provider ecosystem. Use Case components only interact with `LLMProvider` contracts:
- **Gemini (Primary)**: Using the official `google-generativeai` SDK. Standardizes on Gemini models (e.g., `gemini-1.5-flash` or `gemini-1.5-pro`).
- **Ollama (Offline)**: Connects to local Ollama endpoints (e.g., `localhost:11434`) for local development without API costs.
- **OpenRouter (Multi-Model)**: Bridges to open-source models using standard `openai` python clients mapped to OpenRouter endpoints.

---

## 6. Evaluation Concepts
We evaluate agent performance across 4 categories:
1. **Heuristics (Deterministic)**: Check execution budgets (e.g. `TokenBudgetEvaluator`, `CostConstraintEvaluator`), tool syntax validation, and step execution count (detecting tool-call loop crashes).
2. **Retrieval**: Measuring context precision and recall (verifying that the agent query fetched correct records from database).
3. **Cognitive (LLM-as-a-Judge)**:
   - *Faithfulness*: Ensuring the agent's output is based *only* on the provided context (no hallucination).
   - *Groundedness*: Ensuring the response directly addresses user constraints.
   - *Answer Correctness*: Factual and semantic comparison against ground truth.
4. **Safety & Policy**: Checks for prompt injections, system prompt leaks, or leakage of sensitive API keys (PII).

---

## 7. Implementation Assumptions
- **Sequential Agent Steps**: We assume the agent operates in sequential turns (or steps), yielding a list of tool calls and text outputs.
- **Pydantic Validation**: We assume LLM judges might output poorly formatted JSON; thus, we wrap LLM judges in a structured validator that parses outputs into a Pydantic schema and retries on failure.
- **Async Concurrency**: Evaluator executes test cases concurrently using an async event loop, capped by a concurrency semaphore.

---

## 8. Known Limitations
- **SQLite Concurrency**: SQLite database files lock during concurrent write operations. This is mitigated by serializing/queuing write transactions in the SQLite Repository adapter.
- **Static Token Costing**: Token costs are estimated using static input/output rates per model. In production, these should be periodically synced with live billing dashboards.
- **Judge Non-Determinism**: Secondary LLM judges are non-deterministic. To stabilize scores, we enforce `temperature=0.0` and structured schemas.

---

- **UI Dashboard**: While initial dashboards are terminal-based (`rich`), a Next.js frontend or a lightweight static HTML reporter (Jinja2) will serve to share reports across product teams.
- **Regression Analysis**: Implemented in Sprint 3 via [ExperimentEngine](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py), enabling chronological baseline comparison deltas (success rate, latency, cost, and tokens) across agent versions.

---

## 10. Dataset & Experiment Engine (Sprint 3)

### 10.1 Why Version Datasets?
Evaluation datasets (Golden Cases) are code-adjacent. As agents are deployed to production, customer behaviors and edge cases evolve, necessitating dataset updates. Without semantic versioning (`major.minor.patch`) on datasets:
- Regressions cannot be accurately isolated, as changes in evaluation scores could stem from dataset modifications rather than SUT changes.
- Reproducibility is lost. Historical benchmark runs are invalidated if the underlying test cases are silently mutated.

### 10.2 Why Decouple BenchmarkConfig?
By separating [BenchmarkConfig](file:///d:/AI/evalforge/src/domain/entities/benchmark_config.py) from runner execution signatures:
- We promote the Single Responsibility Principle. The [BenchmarkRunner](file:///d:/AI/evalforge/src/use_cases/runners/benchmark_runner.py) only handles execution orchestration, while `BenchmarkConfig` houses parameters.
- We enable reproducibility. A `BenchmarkConfig` can be saved as a configuration file (JSON/YAML) and re-run at any time to guarantee identical execution parameters (concurrency limits, retry policies, evaluators).

### 10.3 Why Treat Experiments as First-Class Citizens?
Evaluating AI agents is an iterative, experimental science:
- An [Experiment](file:///d:/AI/evalforge/src/domain/entities/experiment.py) binds related runs together to test a specific hypothesis (e.g., prompt optimization, model switches, temperature adjustments).
- By storing experiments formally in the [EvaluationRepository](file:///d:/AI/evalforge/src/domain/interfaces/repository.py), teams can query historical progress, calculate deltas relative to a baseline prompt, and automatically generate comparison summaries to decide which agent version is ready for production.

