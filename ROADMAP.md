# ROADMAP — EvalForge

This document maps out our compressed 5-sprint roadmap to build and verify **EvalForge** in approximately one week.

---

## Sprint 1: Pluggable Core Engine & SUT Integration (Days 1–2)
### Objective
Implement concrete LLM adapters and a mock Travel Agent System Under Test (SUT) with access to mock flight, hotel, and weather APIs. This creates the baseline operational environment for evaluations.

### Key Deliverables
- **LLM Adapters** in `src/adapters/llm/`:
  - `GeminiProvider`: Uses `google-generativeai`.
  - `OpenRouterProvider`: Compatibility layer for open-source models using `openai` API patterns.
  - `OllamaProvider`: For local offline evaluations (e.g. `llama3`).
- **Mock Travel SUT** in `src/infrastructure/mock_sut/`:
  - A mock travel agent `TravelAgentSUT` implementing `AgentSUT`.
  - Mock APIs: `flight_search`, `hotel_availability`, `weather_lookup` (intentionally seeded with minor constraints, dates, and bug-prone responses to test evaluations).
- **Verification Gate**:
  - Run integration tests showing the runner executing a mock test case query against `TravelAgentSUT`, executing tool calls, and capturing a complete multi-step `Trajectory`.

---

## Sprint 2: Heuristic & Retrieval Metrics (Days 2–3)
### Objective
Implement deterministic check evaluators (verifying execution limits, dates, budgets, and errors) and context retrieval metrics to check validation databases.

### Key Deliverables
- **Heuristic Evaluators** in `src/use_cases/evaluators/`:
  - `TokenBudgetEvaluator`: Flags runs exceeding token limits.
  - `CostConstraintEvaluator`: Flags runs exceeding price thresholds.
  - `ToolCallValidator`: Audits argument syntax, invalid formats, and checks for "infinite tool call loops".
- **Retrieval Evaluators** in `src/use_cases/evaluators/`:
  - `ContextPrecisionEvaluator`: Measures how relevant retrieved context is compared to ground truth.
  - `ContextRecallEvaluator`: Measures if all necessary ground truth context was retrieved.
- **Verification Gate**:
  - Unit tests in `tests/unit/test_retrieval_metrics.py` asserting correct precision and recall scores against mocked datasets.

---

## Sprint 3: Cognitive Metrics (LLM-as-a-Judge) (Days 3–4)
### Objective
Build advanced cognitive metrics that use a secondary model to grade the quality and correctness of the SUT responses, implementing structured outputs and retry shielding.

### Key Deliverables
- **Cognitive Evaluators** in `src/use_cases/evaluators/`:
  - `FaithfulnessEvaluator`: Audits if SUT's final answer is supported *only* by retrieved contexts (hallucination check).
  - `GroundednessEvaluator`: Checks if SUT response addresses the input query constraints directly.
  - `AnswerCorrectnessEvaluator`: Semantic and factual evaluation comparing the answer against ground truth.
- **Structured Judge Wrapper**:
  - Implements prompt templates and enforces structured JSON parser models (via Pydantic schemas) for LLM judges.
  - Adds retry handlers to recover from format parsing errors.
- **Verification Gate**:
  - Run integration tests comparing LLM judge outputs against pre-defined hallucinated responses, verifying they get low faithfulness scores.

---

## Sprint 4: Safety & Policy Auditing (Days 4–5)
### Objective
Implement safety evaluation metrics to audit policy compliance and build golden dataset versioning to run regression sweeps.

### Key Deliverables
- **Safety Evaluators** in `src/use_cases/evaluators/`:
  - `PromptInjectionEvaluator`: Identifies if the SUT yielded to jailbreaks or prompt injection attacks in the input query.
  - `PolicyComplianceEvaluator`: Grades SUT outputs against custom safety guidelines (e.g. leaking API credentials or system prompts).
- **Dataset Versioning**:
  - Implement metadata schema and version comparisons to compute delta changes (performance improvements or regressions) between agent version A and B.
- **Verification Gate**:
  - Run regression evaluation suite, checking output metrics variance between mock agent versions.

---

## Sprint 5: Database Persistence & Dashboard Reporting (Days 5–6)
### Objective
Provide physical data persistence (SQLite) and build user interfaces (console dashboard and HTML reports) to make EvalForge a complete, visual platform.

### Key Deliverables
- **Database Repository** in `src/adapters/repositories/sqlite_repository.py`:
  - Concrete SQLite implementation of `EvaluationRepository` mapping entities to SQL tables.
- **Console Dashboard** in `src/adapters/cli/`:
  - An interactive, styled CLI display showing real-time run metrics, token costs, and average metrics using `rich`.
- **HTML Report Generator** in `src/adapters/cli/`:
  - Static HTML report compiler using Jinja2 templates, rendering graphs, charts, and detailed trajectories.
- **Verification Gate**:
  - End-to-end integration test executing a benchmark run on a local dataset, saving the results in SQLite, and generating a validated HTML report file.
