# Architecture Blueprint: AI Agent Evaluation Framework

This document outlines the architecture, layer interactions, and design choices of the AI Agent Evaluation Framework.

## 1. Structural Design (Clean Architecture)

We strictly separate our codebase into four layers as dictated by Clean Architecture principles. Dependencies only point inwards:

```
            ┌──────────────────────────────────────────────┐
            │                 Infrastructure               │
            │  (Database connections, HTTP clients, stubs) │
            └──────────────────────┬───────────────────────┘
                                   │ (implements)
            ┌──────────────────────▼───────────────────────┐
            │                    Adapters                  │
            │    (Gemini API, SQLite Repo, CLI View)       │
            └──────────────────────┬───────────────────────┘
                                   │ (implements / uses)
            ┌──────────────────────▼───────────────────────┐
            │                    Use Cases                 │
            │   (BenchmarkRunner, FaithfulnessEvaluator)   │
            └──────────────────────┬───────────────────────┘
                                   │ (uses)
            ┌──────────────────────▼───────────────────────┐
            │                     Domain                   │
            │ (Entities, Value Objects, Interfaces/Specs)  │
            └──────────────────────────────────────────────┘
```

### Domain Layer (`src/domain/`)
- Contains the core, immutable business models.
- **Entities**: `EvaluationRun`, `Trajectory`, `Step`, `GoldenDataset`, `GoldenTestCase`.
- **Value Objects**: `TokenUsage`, `Cost`, `Latency`, `MetricScore`.
- **Interfaces**: Abstract representations of LLM clients (`LLMProvider`), storage (`EvaluationRepository`), and metrics (`BaseEvaluator`).
- *Constraint*: No third-party dependencies are imported here, except Pydantic (for types) and basic standard Python modules.

### Use Cases Layer (`src/use_cases/`)
- Contains application-specific business rules. Orchestrates domain objects and triggers actions.
- **Benchmark Runner**: Coordinates executing the SUT (System Under Test) on golden datasets, collecting trajectories, and storing them.
- **Evaluators**: Use cases representing specific metrics (e.g. `GroundednessEvaluator` uses an `LLMProvider` to assess a `Trajectory`).

### Adapters Layer (`src/adapters/`)
- Bridges our use cases with concrete tools, libraries, and external systems.
- **LLM**: Concrete adapters such as [GeminiProvider](file:///d:/AI/evalforge/src/adapters/llm/gemini.py), [OllamaProvider](file:///d:/AI/evalforge/src/adapters/llm/ollama.py), and [OpenRouterProvider](file:///d:/AI/evalforge/src/adapters/llm/openrouter.py) implementing [LLMProvider](file:///d:/AI/evalforge/src/domain/interfaces/llm_provider.py).
- **Repositories**: Concrete SQL persistence via [SqliteEvaluationRepository](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py) implementing [EvaluationRepository](file:///d:/AI/evalforge/src/domain/interfaces/repository.py).
- **CLI**: Entrypoints for commands (`run-evaluation`, `create-dataset`).

### Infrastructure Layer (`src/infrastructure/`)
- Houses global environment variables configurations, third-party client bootstrapper tools, and low-level helpers.
- *Constraint*: The infrastructure layer of the core framework remains strictly domain-independent.

### Reference Implementation (`examples/travel_agent/`)
Demonstrates how to plug any AI Agent system into EvalForge:
- **Travel Agent SUT**: [TravelAgentSUT](file:///d:/AI/evalforge/examples/travel_agent/travel_agent_sut.py) implementing the [AgentSUT](file:///d:/AI/evalforge/src/domain/interfaces/sut.py) contract. Coordinates multi-turn reasoning steps for travel requests.
- **Travel Simulation Layer**: Deterministic catalog services under [services.py](file:///d:/AI/evalforge/examples/travel_agent/services.py) including:
  - `FlightService`: Searches flight listings.
  - `HotelService`: Searches hotel listings.
  - `WeatherService`: Fetches mock weather forecasts.
  - `CurrencyService`: Converts exchange rates.
  - `AttractionsService`: Retrieves sightseeing lists.
  - `BookingPolicyService`: Checks corporate policies.
  - `UserProfileService`: Retrieves user budgets/tags.

---


## 2. Core Domain Data Flow

During a single evaluation bench run:

```
┌──────────────┐      1. Load Cases      ┌─────────────────┐
│  Repository  ├────────────────────────>│ BenchmarkRunner │
└──────────────┘                         └────────┬────────┘
                                                  │
                                                  │ 2. Run Test Cases
                                                  ▼
┌──────────────┐      3. Interact        ┌─────────────────┐
│   Mock SUT   │<────────────────────────┤   Travel SUT    │
│  (APIs/DB)   │                         │  Agent Wrapper  │
└──────────────┘                         └────────┬────────┘
                                                  │ 4. Extract Trajectory
                                                  ▼
┌──────────────┐      5. Score           ┌─────────────────┐
│  Evaluators  │<────────────────────────┤   Trajectory    │
│  (LLM Judge) │                         │    Metadata     │
└──────────┬───┘                         └────────┬────────┘
           │                                      │
           └──────────────────┬───────────────────┘
                              │ 6. Save Results
                              ▼
                      ┌──────────────┐
                      │  Repository  │
                      └──────────────┘
```

## 3. Pluggable Providers
To remain provider-agnostic, Use Cases interact solely with `LLMProvider`. Providers must handle authentication internally (using keys from environment variables like `GEMINI_API_KEY`) and map their outputs back to domain models.

---

## 4. Metrics Engine

The Metrics Engine uses a decoupled, registry-based flow to score agent trajectories without coupling the core execution runner (`BenchmarkRunner`) to concrete metric implementations.

### 4.1 Registry Pattern
The `MetricRegistry` class acts as the centralized container:
- All evaluators (such as `LatencyEvaluator` or custom cognitive LLM judges) inherit from the [BaseEvaluator](file:///d:/AI/evalforge/src/domain/interfaces/evaluator.py) contract and are registered in [MetricRegistry](file:///d:/AI/evalforge/src/use_cases/metrics/registry.py).
- `BenchmarkRunner` retrieves evaluators dynamically from the registry using metric name strings. It never instantiates concrete metrics itself, satisfying Dependency Inversion.

### 4.2 Aggregation Flow
Aggregation of runs is separated from evaluation execution:
- The [AggregationEngine](file:///d:/AI/evalforge/src/use_cases/metrics/aggregation.py) takes individual `TestCaseEvaluation` outputs, sums tokens/costs/latencies, averages evaluator scores, and generates the final `EvaluationRun.summary` dictionary.
- This decoupling allows developers to easily extend or adjust calculations (e.g. adding P95 latency, stddev, or weights) in a single class.

### 4.3 Extension Points
To add a new metric:
1. Create a class that implements `BaseEvaluator` (defining its unique `name` and `evaluate` method).
2. Register the instance in the `MetricRegistry` using `registry.register(new_evaluator)`.
3. Pass the registry to `BenchmarkRunner`. The runner will automatically discover and run it.

---

## 5. Dataset Engine

The Dataset Engine makes evaluation datasets first-class Citizens in EvalForge, providing tools for version control, syntax loading, and semantic validation.

```
                  ┌─────────────────┐
                  │  DatasetLoader  │
                  └────────┬────────┘
                           │ (parses JSON/JSONL)
                           ▼
                  ┌─────────────────┐
                  │ GoldenDataset   │
                  └────────┬────────┘
                           │ (validates)
                           ▼
                  ┌─────────────────┐
                  │DatasetValidator │
                  └────────┬────────┘
                           │ (registers)
                           ▼
                  ┌─────────────────┐
                  │ DatasetRegistry │
                  └─────────────────┘
```

- **[DatasetRegistry](file:///d:/AI/evalforge/src/use_cases/datasets/registry.py)**: Manages and indexes datasets, ensuring uniqueness using a compound key of `(dataset_id, version)`. It allows lookups by specific versions or automatic resolution to the latest semantic version.
- **[DatasetValidator](file:///d:/AI/evalforge/src/use_cases/datasets/validator.py)**: Audits the datasets, ensuring required fields (`dataset_id`, `name`, `version`, `case_id`, `input_query`) exist, that test case IDs are unique, that versions conform to semantic versioning (SemVer), and that constraints values are typed correctly.
- **[DatasetLoader](file:///d:/AI/evalforge/src/use_cases/datasets/loader.py)**: Reads and parses datasets from `JSON` (complete dataset schema) and `JSONL` (where each line is a test case, optionally prepended with a metadata line or complemented by parameter overrides). Line numbers are tracked to throw highly diagnostic errors on parsing/schema violations.

---

## 6. Experiment Engine

The Experiment Engine coordinates the comparison, history tracking, and reporting of multiple evaluation runs testing specific hypotheses.

```
 ┌─────────────────┐       ┌─────────────────┐
 │  EvaluationRun  │       │  EvaluationRun  │
 │     (Run A)     │       │     (Run B)     │
 └────────┬────────┘       └────────┬────────┘
          │                         │
          └───────────┬─────────────┘
                      │ (aggregates)
                      ▼
             ┌─────────────────┐
             │   Experiment    │
             └────────┬────────┘
                      │ (analyzes)
                      ▼
             ┌─────────────────┐
             │ExperimentEngine │
             └────────┬────────┘
                      ├───────────────────────────┐
                      ▼                           ▼
            ┌──────────────────┐        ┌──────────────────┐
            │ExperimentComparer│        │ SummaryGenerator │
            │ (delta analysis) │        │ (markdown report)│
            └──────────────────┘        └──────────────────┘
```

- **[Experiment](file:///d:/AI/evalforge/src/domain/entities/experiment.py)**: A domain entity grouping multiple `EvaluationRun`s, enabling regression sweeps and comparison.
- **[ExperimentEngine](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py)**: Coordinates creation, run registration, persistence, and reporting of experiments.
- **[ExperimentComparer](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py)**: Takes multiple runs and calculates performance deltas (success rates, token counts, costs, and latencies) against a baseline (the first chronological run).
- **[ExperimentSummaryGenerator](file:///d:/AI/evalforge/src/use_cases/experiments/engine.py)**: Formats the comparison results, rendering a clean, rich markdown summary illustrating baseline comparison deltas and highlighting the best-performing configuration.

---

## 7. LLM Judge Engine

The LLM Judge Engine provides a reusable and extensible architecture for qualitative evaluators (LLM-as-a-judge) to grade SUT behaviors.

```
                    ┌─────────────────────────┐
                    │     BenchmarkRunner     │
                    └────────────┬────────────┘
                                 │ (executes)
                                 ▼
                    ┌─────────────────────────┐
                    │      BaseLLMJudge       │
                    └────────────┬────────────┘
                                 │ (delegates)
                                 ▼
                    ┌─────────────────────────┐
                    │     LLMJudgeEngine      │
                    └────────────┬────────────┘
                                 ├────────────────────────────┐
                                 ▼                            ▼
                    ┌─────────────────────────┐   ┌─────────────────────────┐
                    │   LLMProvider (Adapter) │   │   JudgePromptTemplate   │
                    └─────────────────────────┘   └─────────────────────────┘
```

### 7.1 Key Components
- **[BaseLLMJudge](file:///d:/AI/evalforge/src/use_cases/judges/base.py)**: An abstract base class that implements `BaseEvaluator`. Any LLM Judge inherits from this base class, making it completely compatible with the framework's standard `MetricRegistry` and `BenchmarkRunner` without any architectural changes.
- **[LLMJudgeEngine](file:///d:/AI/evalforge/src/use_cases/judges/engine.py)**: A reusable execution engine that handles prompt construction, LLM provider interaction, structured Pydantic parsing (`LLMJudgeOutputSchema`), error handling, and confidence tracking. It attempts structured responses first and falls back to text generation and manual JSON block extraction if parsing fails, retrying with exponential backoff on transient errors.
- **[JudgeRegistry](file:///d:/AI/evalforge/src/use_cases/judges/registry.py)**: A dedicated registry for registering, retrieving, and discovering LLM Judges, enforcing uniqueness by preventing duplicate judge name registrations.
- **[JudgePromptTemplate](file:///d:/AI/evalforge/src/use_cases/judges/templates.py)**: Reusable prompt structures separating system instructions, evaluation prompts, and scoring rubrics from formatting logic.

### 7.2 Initial Judges
- **[FaithfulnessJudge](file:///d:/AI/evalforge/src/use_cases/judges/faithfulness.py)**: Checks if the SUT response is supported *only* by the retrieved context.
- **[GroundednessJudge](file:///d:/AI/evalforge/src/use_cases/judges/groundedness.py)**: Checks if the SUT response addresses the query and satisfies constraints.
- **[AnswerCorrectnessJudge](file:///d:/AI/evalforge/src/use_cases/judges/correctness.py)**: Evaluates semantic and factual correctness against reference ground truth.
- **[HallucinationJudge](file:///d:/AI/evalforge/src/use_cases/judges/hallucination.py)**: Scans specifically for fabricated claims or contradictions compared to the context.

### 7.3 Extension Points
To add a new LLM-based judge:
1. Create a class that inherits from `BaseLLMJudge`.
2. Define a `JudgePromptTemplate` containing custom system instructions and scoring rubrics.
3. Implement `prepare_variables(self, test_case, trajectory)` to extract prompt parameters.
4. Register the judge in the `JudgeRegistry` and `MetricRegistry`.

---

## 8. Platform & Productization

EvalForge is productized as a dual-service containerized platform exposing the evaluation engine over REST APIs and a visual dashboard.

```
       ┌────────────────────────┐
       │   Next.js Dashboard    │
       │ (Port 3000 / React)    │
       └───────────┬────────────┘
                   │ (HTTP REST / JSON)
                   ▼
       ┌────────────────────────┐
       │    FastAPI Backend     │
       │ (Port 8000 / Uvicorn)  │
       └───────────┬────────────┘
                   │ (Orchestrates)
                   ▼
       ┌────────────────────────┐
       │     EvalForge Core     │
       │ (Repo, Runner, Judges) │
       └────────────────────────┘
```

### 8.1 FastAPI Backend Adapter
The REST API resides in `src/adapters/api/app.py` and exposes:
- **Health Checks**: `/health` verifying service availability.
- **Dataset Catalog**: endpoints to list, view, and register golden datasets.
- **Experiment Engine**: endpoints to create and list experiment sweeps, resolving performance deltas.
- **Async Execution**: `POST /api/benchmarks/run` triggers evaluations asynchronously via FastAPI `BackgroundTasks`, returning a `run_id` immediately to avoid blocking client threads.
- **Execution Reports**: endpoints to download formatted markdown run summaries.

### 8.2 Next.js Frontend
An interactive Single Page App inside the `frontend/` directory using TypeScript:
- **Overview Dashboard**: displays total evaluations, success rate trends, and aggregated cost/latency charts.
- **Test Hub**: launches execution runs, configures max retries, and defines concurrency constraints.
- **Trajectory Inspector**: explores step-by-step SUT thoughts, tool calls, and LLM judge reasoning logs.

### 8.3 Reporting Engine
The `MarkdownReportGenerator` inside `src/use_cases/reporting/markdown.py` compiles single-run execution summaries containing:
- Executive summary metrics (Success rate, token count, cost, average latency).
- Evaluator tables comparing deterministic check results against qualitative cognitive judge scores.
- Trajectory tracing and trace comments.

### 8.4 Observability
- **JSON Structured Logging**: `JSONFormatter` in `src/infrastructure/logging/formatter.py` serializes all Python logs as machine-parseable JSON lines.
- **Trace Context**: `BenchmarkRunner` injects metadata context (`benchmark_id`, `experiment_id`, `dataset_version`, `provider`, `retries`, `latency`, `outcome`) into the logging pipeline.


