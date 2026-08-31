# EvalForge

**A benchmark-driven evaluation and observability platform for agentic AI systems.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-000000?style=flat&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat&logo=githubactions&logoColor=white)](https://github.com/jacobjerryarackal/evalforge/actions)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

---

## Live Links

* **Repository**: [github.com/jacobjerryarackal/evalforge](https://github.com/jacobjerryarackal/evalforge)
* **Frontend Dashboard**: [evalforge.vercel.app](https://evalforge.vercel.app)
* **Backend REST API**: [evalforge-backend.onrender.com](https://evalforge-backend.onrender.com)
* **Interactive API Docs (Swagger)**: [evalforge-backend.onrender.com/docs](https://evalforge-backend.onrender.com/docs)
* **Service Health Check**: [evalforge-backend.onrender.com/health](https://evalforge-backend.onrender.com/health)

---

## 1. Executive Summary

**EvalForge** is an open-source, model-agnostic evaluation, benchmarking, and observability platform engineered for autonomous, tool-calling AI agents. 

Traditional software testing verifies determinism: a known input executes a fixed codepath yielding an expected output. Autonomous AI agents break this paradigm. They operate statefully across multiple turns, reason dynamically, select external tools, format API parameters on the fly, and interpret retrieved unstructured data. 

EvalForge shifts evaluation from black-box output assertions to **full-trajectory observability**. It executes agents against version-controlled golden datasets, captures multi-turn intermediate execution traces (thoughts, tool calls, arguments, observations, token usage, latency, and cost), scores them via deterministic constraints alongside cognitive LLM-as-a-judge rubrics, persists runs in PostgreSQL or SQLite, and computes comparative regression deltas in an interactive Next.js dashboard.

---

## 2. The Problem

### Why Traditional Testing Fails for Agentic AI

In classical software engineering, testing follows a deterministic pipeline:

```
Input  ───>  Function / Service  ───>  Output  ───>  Assertion (Pass / Fail)
```

In agentic architectures, testing only the final string output creates a dangerous false sense of reliability. An agent system operates as a stochastic, multi-step decision loop:

```
User Request
     │
     ▼
 Reasoning (LLM)
     │
     ▼
 Tool Selection
     │
     ▼
 Tool Arguments Generation
     │
     ▼
 Tool Execution (External API / DB)
     │
     ▼
 Observation & Context Ingestion
     │
     ▼
 Next Decision / Additional Tool Calls (Loop)
     │
     ▼
 Final Output Response
```

### The "Correct Answer, Flawed Trajectory" Failure Mode

An agent can return a response that appears textually correct while masking critical operational failures:
* **Tool Misrouting**: Booking a flight using a mock notification tool rather than the flight reservation API.
* **Schema & Argument Errors**: Passing malformed dates, invalid currencies, or hallucinated IDs to external APIs.
* **Unfaithful Grounding**: Generating a correct answer by hallucinating facts rather than grounding them in retrieved search snippets.
* **Budget & Latency Blowouts**: Looping repeatedly through unnecessary tool calls, consuming hundreds of thousands of tokens and taking 20+ seconds to resolve a simple query.
* **Silent Regressions**: A minor prompt tweak or model upgrade (e.g., from `gemini-1.5-flash` to a newer model) fixing one edge case while subtly degrading tool calling precision across 15% of historical test scenarios.

Testing agentic AI requires evaluating **the entire execution trajectory**, not just the final return value.

---

## 3. Why Did We Choose This Problem?

1. **The Shift to Autonomous Tool-Using Systems**: Modern AI engineering is transitioning from static prompt/response generation to autonomous agents integrated with production APIs, databases, and enterprise tools.
2. **Untracked Failure Modes**: In agent systems, failures rarely manifest as explicit runtime exceptions. Instead, they manifest as hallucinations, improper tool calls, context omissions, and latency degradation.
3. **Operational & Financial Constraints**: Autonomous reasoning loops risk unbounded latency and token consumption without continuous monitoring against hard budgetary constraints.
4. **Lack of Repeatable Engineering Discipline**: Many teams evaluate agents through subjective manual inspection ("vibes-based testing"). Evaluation must become a repeatable, quantitative engineering discipline backed by versioned benchmarks and regression delta analysis.

---

## 4. Why EvalForge?

EvalForge provides a unified platform that bridges the gap between raw execution traces and quantitative evaluation:

* **Trajectory-First Observability**: Records every intermediate thought, tool invocation, argument schema, tool observation, step latency, step token usage, and step cost.
* **Dual-Pronged Evaluation**:
  * **Deterministic Heuristics**: Programmatic checks for latency ceilings, token budgets, USD cost limits, tool selection accuracy, and context retrieval recall/precision.
  * **Cognitive LLM Judges**: Robust rubrics for faithfulness, groundedness, answer correctness, and hallucination detection.
* **Versioned Golden Datasets**: Repeatable, schema-validated benchmarks with expected tool calls, ground-truth context, and multi-dimensional constraints.
* **Experiment & Regression Tracking**: Automatic delta computation ($\Delta \text{Success Rate}$, $\Delta \text{Latency}$, $\Delta \text{Cost}$, $\Delta \text{Metric Score}$) against established baselines.
* **Dual Database Portability**: Seamless switching between zero-config SQLite for local development and PostgreSQL with connection pooling for production.
* **Interactive UI & REST API**: Next.js dashboard for step-by-step trajectory inspection and FastAPI endpoints for automated pipeline integration.

---

## 5. Inspiration — Booking.com

EvalForge was conceptually inspired by the public engineering philosophy, data science literature, and experimentation culture demonstrated by **Booking.com** around large-scale empirical evaluation and evidence-based software evolution.

### Conceptual Influences
1. **Experimentation as an Engineering Discipline**: In mature engineering cultures like Booking.com, product and algorithmic decisions are guided by empirical evidence rather than subjective impressions. EvalForge replaces *"Does this new agent prompt feel better?"* with *"What are the exact metric deltas across our 10 golden benchmark suites?"*
2. **Multi-Dimensional Quality Measurement**: Evaluating complex booking and travel workflows requires isolating retrieval precision, tool orchestration accuracy, and constraint compliance into independent, quantifiable signals.
3. **Continuous Regression Detection**: Upgrading models or modifying agent instructions requires automated delta comparisons against established baselines to prevent silent degradation.
4. **Evidence-Driven AI Development**: AI agent development requires reproducible benchmark runs where every decision is backed by persistent trajectory data.

> [!NOTE]
> **Disclaimer**: EvalForge is an independently developed open-source project inspired by publicly available engineering articles and experimentation methodologies discussed by Booking.com. It is **not** affiliated with, sponsored by, or endorsed by Booking.com, and does not use any proprietary Booking.com source code, datasets, or internal systems.
>
> *Reference*: [Booking.com Tech Blog & Engineering Publications](https://medium.com/booking-com-development)

---

## 6. What Does EvalForge Actually Do?

The diagram below illustrates the end-to-end lifecycle executed by EvalForge:

```mermaid
flowchart TD
    A[Benchmark Definition] --> B[Golden Dataset]
    B --> C[Evaluation Run Trigger]
    C --> D[BenchmarkRunner Orchestrator]
    D --> E[Agent SUT Execution]
    E --> F[Capture Execution Trajectory]
    F --> G1[Deterministic Evaluators]
    F --> G2[LLM-as-a-Judge Engine]
    G1 --> H[Metric Aggregation Engine]
    G2 --> H
    H --> I[TestCase Evaluation Records]
    I --> J[Evaluation Repository]
    J --> K[(PostgreSQL / SQLite)]
    K --> L[Experiment Engine]
    L --> M[Regression Delta Analysis]
    M --> N[Next.js Dashboard & REST API]
```

---

## 7. System Design

EvalForge is designed as a decoupled, modular system separating the web dashboard, API layer, evaluation use cases, domain logic, and external infrastructure:

```mermaid
flowchart TB
    subgraph ClientLayer [Client Layer]
        UI[Next.js 14 Dashboard]
        APIClient[HTTP / REST Client]
    end

    subgraph APILayer [API Layer - FastAPI]
        Router[REST API Endpoints]
        BGTasks[FastAPI BackgroundTasks Worker]
    end

    subgraph ApplicationLayer [Application / Use Cases]
        Runner[BenchmarkRunner]
        ExpEngine[ExperimentEngine]
        Registry[MetricRegistry]
        AggEngine[AggregationEngine]
        JudgeEngine[LLMJudgeEngine]
    end

    subgraph SUTLayer [System Under Test Layer]
        SUTInterface[AgentSUT Interface]
        TravelSUT[TravelAgentSUT Reference SUT]
        Tools[Mock Travel Services / APIs]
    end

    subgraph EvaluationLayer [Evaluation Engine]
        DetMetrics[Deterministic Evaluators: Latency, Cost, Tokens, ToolCalling, Context]
        LLMJudges[Cognitive Judges: Faithfulness, Groundedness, Correctness, Hallucination]
    end

    subgraph AdapterLayer [Adapters & Persistence]
        RepoInterface[EvaluationRepository Interface]
        PGRepo[PostgresEvaluationRepository]
        SqliteRepo[SqliteEvaluationRepository]
        LLMProviders[LLM Provider Adapters: Gemini, Ollama, OpenRouter]
    end

    subgraph StorageLayer [Storage Layer]
        Postgres[(PostgreSQL 15)]
        SQLite[(SQLite DB)]
    end

    UI --> Router
    Router --> BGTasks
    BGTasks --> Runner
    Router --> ExpEngine
    Runner --> TravelSUT
    TravelSUT --> Tools
    Runner --> Registry
    Registry --> DetMetrics
    Registry --> JudgeEngine
    JudgeEngine --> LLMJudges
    LLMJudges --> LLMProviders
    Runner --> AggEngine
    Runner --> RepoInterface
    ExpEngine --> RepoInterface
    RepoInterface --> PGRepo
    RepoInterface --> SqliteRepo
    PGRepo --> Postgres
    SqliteRepo --> SQLite
```

---

## 8. High-Level Design (HLD)

EvalForge strictly adheres to **Clean Architecture** and **Domain-Driven Design (DDD)** principles to keep domain logic isolated from frameworks and storage engines:

```mermaid
flowchart TD
    subgraph Infrastructure [Infrastructure Layer]
        Logging[Structured JSON Logging]
        ConnectionPool[psycopg2 ThreadedConnectionPool]
        EnvConfig[python-dotenv Configuration]
    end

    subgraph Adapters [Adapters Layer]
        FastAPIApp[FastAPI REST Controllers]
        PostgresAdapter[PostgresEvaluationRepository]
        SqliteAdapter[SqliteEvaluationRepository]
        GeminiAdapter[GeminiProvider]
        OllamaAdapter[OllamaProvider]
        OpenRouterAdapter[OpenRouterProvider]
    end

    subgraph UseCases [Use Cases Layer]
        RunnerUC[BenchmarkRunner]
        ExperimentUC[ExperimentEngine]
        MetricRegistryUC[MetricRegistry]
        JudgeEngineUC[LLMJudgeEngine]
        AggregatorUC[AggregationEngine]
        DatasetValidatorUC[DatasetValidator]
    end

    subgraph Domain [Domain Layer - Pure Business Logic]
        RunEntity[EvaluationRun]
        DatasetEntity[GoldenDataset & GoldenTestCase]
        TrajectoryEntity[Trajectory, Step, ToolCall]
        ExperimentEntity[Experiment]
        VO[Value Objects: TokenUsage, Cost, Latency]
        Interfaces[Interfaces: EvaluationRepository, BaseEvaluator, AgentSUT, LLMProvider]
    end

    Infrastructure --> Adapters
    Adapters --> UseCases
    UseCases --> Domain
```

### Layer Responsibilities
* **Domain Layer (`src/domain/`)**: Pure Pydantic entities, immutable value objects, and abstract interface contracts (`EvaluationRepository`, `BaseEvaluator`, `AgentSUT`, `LLMProvider`). Contains zero external framework dependencies.
* **Use Cases Layer (`src/use_cases/`)**: Business logic orchestrating benchmark runs, bounded concurrency execution, metric evaluation, LLM judge execution with fallback parsing, summary statistics calculation, and experiment delta comparisons.
* **Adapters Layer (`src/adapters/`)**: Concrete implementations of domain interfaces:
  * Repositories: `PostgresEvaluationRepository` and `SqliteEvaluationRepository`.
  * LLM Providers: `GeminiProvider` (Google Generative AI SDK + Mock Mode), `OllamaProvider` (Local LLM via HTTPX), `OpenRouterProvider` (OpenAI-compatible client).
  * API: FastAPI routers and serialization wrappers.
* **Infrastructure Layer (`src/infrastructure/`)**: Thread pooling, database connection pools, environment configuration, and structured logging.
* **Client Layer (`frontend/`)**: Next.js 14 web application built with TypeScript, React Query, Recharts, and Tailwind CSS.

---

## 9. Low-Level Design (LLD)

### Class Diagram

The class diagram below depicts the core interfaces, domain models, evaluators, and repository implementations in the codebase:

```mermaid
classDiagram
    class AgentSUT {
        <<interface>>
        +version: str
        +run(input_query: str) Trajectory
    }

    class TravelAgentSUT {
        -flight_service: FlightService
        -hotel_service: HotelService
        -weather_service: WeatherService
        +version: str
        +run(input_query: str) Trajectory
    }

    class LLMProvider {
        <<interface>>
        +generate_text(prompt, system_instruction, temperature, max_tokens) str
        +generate_structured(prompt, response_schema, system_instruction, temperature, max_tokens) BaseModel
    }

    class GeminiProvider {
        +api_key: str
        +model_name: str
        +mock_mode: bool
        +generate_text(...) str
        +generate_structured(...) BaseModel
    }

    class BaseEvaluator {
        <<interface>>
        +name: str
        +evaluate(test_case: GoldenTestCase, trajectory: Trajectory) MetricResult
    }

    class LatencyEvaluator {
        +name: str
        +evaluate(...) MetricResult
    }

    class ToolCallingEvaluator {
        +name: str
        +evaluate(...) MetricResult
    }

    class ContextRecallEvaluator {
        +name: str
        +evaluate(...) MetricResult
    }

    class LLMJudgeEngine {
        -provider: LLMProvider
        -max_retries: int
        +execute(template, variables, output_schema) JudgeResult
        -_parse_json_from_text(text: str) dict
    }

    class BenchmarkRunner {
        -repository: EvaluationRepository
        -registry: MetricRegistry
        -aggregation_engine: AggregationEngine
        +run_benchmark(run_id, config, sut) EvaluationRun
        -_evaluate_case_bounded(case, sut, semaphore, config) TestCaseEvaluation
    }

    class EvaluationRepository {
        <<interface>>
        +save_dataset(dataset: GoldenDataset)
        +get_dataset(dataset_id: str, version: str) GoldenDataset
        +list_datasets() list~GoldenDataset~
        +save_run(run: EvaluationRun)
        +get_run(run_id: str) EvaluationRun
        +list_runs(dataset_id: str) list~EvaluationRun~
        +save_experiment(experiment: Experiment)
        +get_experiment(experiment_id: str) Experiment
        +list_experiments() list~Experiment~
    }

    class PostgresEvaluationRepository {
        -pool: ThreadedConnectionPool
        -database_url: str
        -_get_connection() ContextManager
        -_init_db()
        +save_dataset(...)
        +save_run(...)
        +save_experiment(...)
    }

    class SqliteEvaluationRepository {
        -db_path: str
        -_init_db()
        +save_dataset(...)
        +save_run(...)
        +save_experiment(...)
    }

    class Trajectory {
        +steps: list~Step~
        +total_token_usage: TokenUsage
        +total_cost: Cost
        +total_latency: Latency
        +add_step(step: Step)
        +final_response: str
        +all_tool_calls: list~ToolCall~
    }

    class Step {
        +step_number: int
        +thought: str
        +tool_calls: list~ToolCall~
        +observation: Any
        +response: str
        +token_usage: TokenUsage
        +cost: Cost
        +latency: Latency
    }

    class ToolCall {
        +tool_name: str
        +arguments: dict
        +success: bool
        +error: str
    }

    class EvaluationRun {
        +run_id: str
        +dataset_id: str
        +dataset_version: str
        +sut_version: str
        +cases: list~TestCaseEvaluation~
        +summary: dict
        +compute_summary()
    }

    AgentSUT <|.. TravelAgentSUT
    LLMProvider <|.. GeminiProvider
    BaseEvaluator <|.. LatencyEvaluator
    BaseEvaluator <|.. ToolCallingEvaluator
    BaseEvaluator <|.. ContextRecallEvaluator
    EvaluationRepository <|.. PostgresEvaluationRepository
    EvaluationRepository <|.. SqliteEvaluationRepository
    BenchmarkRunner --> AgentSUT : executes
    BenchmarkRunner --> EvaluationRepository : persists
    BenchmarkRunner --> Trajectory : evaluates
    LLMJudgeEngine --> LLMProvider : uses
    EvaluationRun o-- Trajectory : contains
    Trajectory *-- Step : contains
    Step *-- ToolCall : contains
```

---

## 10. End-to-End Execution Lifecycle

The sequence diagram below details what happens when a benchmark run is initiated from the client:

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer / Dashboard
    participant API as FastAPI Router (/api/benchmarks/run)
    participant BG as BackgroundTasks Worker
    participant Runner as BenchmarkRunner
    participant SUT as Agent SUT (TravelAgentSUT)
    participant Registry as MetricRegistry
    participant Judge as LLMJudgeEngine
    participant LLM as LLM Provider (Gemini / Ollama)
    participant Repo as Postgres / SQLite Repository
    participant DB as PostgreSQL / SQLite DB

    User->>API: POST /api/benchmarks/run (dataset_id, version, concurrency)
    API->>Repo: get_dataset(dataset_id, version)
    Repo->>DB: SELECT * FROM golden_datasets
    DB-->>Repo: GoldenDataset
    Repo-->>API: GoldenDataset
    API->>BG: Add task: _run_benchmark_task(run_id, dataset, sut)
    API-->>User: 202 Accepted {"status": "running", "run_id": "run-xyz"}

    BG->>Runner: run_benchmark(run_id, config, sut)
    loop For each test case in dataset (Bounded Concurrency via Semaphore)
        Runner->>SUT: run(case.user_query)
        loop Multi-Turn Execution
            SUT->>SUT: Generate Thought
            SUT->>SUT: Execute Tool Calls & Get Observations
        end
        SUT-->>Runner: Trajectory (Steps, ToolCalls, Latency, Cost, Tokens)
        
        Runner->>Registry: evaluate_all(case, trajectory)
        par Deterministic Evaluators
            Registry->>Registry: Run Latency, TokenUsage, Cost, ToolCalling, ContextRecall/Precision
        and Cognitive Judges
            Registry->>Judge: execute(Faithfulness / Groundedness / Correctness / Hallucination)
            Judge->>LLM: generate_structured(prompt, schema)
            alt Structured Generation Succeeds
                LLM-->>Judge: Valid JSON Output
            else Structured Generation Fails
                Judge->>LLM: generate_text(prompt)
                LLM-->>Judge: Raw text response
                Judge->>Judge: _parse_json_from_text(regex fallback)
            end
            Judge-->>Registry: JudgeResult (score, reasoning, confidence)
        end
        Registry-->>Runner: dict[str, MetricResult]
    end

    Runner->>Runner: Compute EvaluationRun Summary (success_rate, avg_latency, total_cost)
    Runner->>Repo: save_run(run)
    Repo->>DB: INSERT INTO evaluation_runs (run_id, cases, summary, ...)
    DB-->>Repo: OK
    
    User->>API: GET /api/runs/{run_id}
    API->>Repo: get_run(run_id)
    Repo->>DB: SELECT * FROM evaluation_runs WHERE run_id = %s
    DB-->>Repo: EvaluationRun record
    Repo-->>API: EvaluationRun
    API-->>User: Run details, summary cards, and trajectory traces
```

---

## 11. Agent Trajectory Model

EvalForge records execution traces using a hierarchical domain model that captures granular telemetry across every reasoning turn:

```mermaid
flowchart TD
    UserQuery[GoldenTestCase User Query] --> TrajectoryModel[Trajectory Object]
    
    subgraph TrajectoryModel [Trajectory Model]
        Step1[Step 1]
        Step2[Step 2]
        StepN[Step N]
        Totals[Total Latency, Total Cost, Total Token Usage]
    end

    subgraph StepBreakdown [Step Granular Telemetry]
        Thought[Thought: Internal Reasoning String]
        ToolCalls[Tool Calls: Array of ToolCall]
        Obs[Observation: API Output Payload]
        Resp[Final Response: Terminal Output]
        Metrics[Step Latency, Step Cost, Step TokenUsage]
    end

    subgraph ToolCallBreakdown [ToolCall Telemetry]
        ToolName[tool_name: e.g. search_flights]
        Args[arguments: Structured Dict Payload]
        Status[success: Boolean]
        Error[error: Error String or None]
    end

    Step1 --> Thought
    Step1 --> ToolCalls
    Step1 --> Obs
    Step1 --> Resp
    Step1 --> Metrics
    ToolCalls --> ToolCallBreakdown
```

### Telemetry Fields Captured per Step

| Field | Type | Description |
| :--- | :--- | :--- |
| `step_number` | `int` | 1-indexed sequential step identifier. |
| `thought` | `str \| None` | Intermediate chain-of-thought or reasoning string produced by the LLM. |
| `tool_calls` | `list[ToolCall]` | List of tools invoked in this step (tool name, JSON arguments, success boolean, error message). |
| `observation` | `str \| dict \| None` | Structured response or error payload returned by external APIs/tools. |
| `response` | `str \| None` | Terminal text answer delivered to the user (present on final step). |
| `token_usage` | `TokenUsage` | Prompt tokens, completion tokens, and total tokens consumed in this turn. |
| `cost` | `Cost` | Financial cost in USD calculated from model token pricing tables. |
| `latency` | `Latency` | Execution duration in seconds for this turn. |
| `metadata` | `dict[str, Any]` | Provider-specific headers, raw logs, or execution context. |

---

## 12. Evaluation Methodology

EvalForge employs a two-tier evaluation architecture combining deterministic programmatic rules with cognitive LLM judges:

```
                               ┌────────────────────────────────────────────────────────┐
                               │                 Evaluation Engine                      │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┴─────────────────────────────────────┐
                    ▼                                                                           ▼
┌───────────────────────────────────────┐                                   ┌───────────────────────────────────────┐
│        Deterministic Metrics          │                                   │          LLM-as-a-Judge               │
├───────────────────────────────────────┤                                   ├───────────────────────────────────────┤
│ • Latency Constraints                 │                                   │ • Faithfulness                        │
│ • Token Usage Budgets                 │                                   │ • Groundedness                        │
│ • Financial Cost Ceilings             │                                   │ • Answer Correctness                  │
│ • Tool Calling & Schema Validation    │                                   │ • Hallucination Detection             │
│ • Context Recall (Overlap Heuristic)  │                                   │ • Resilient Fallback Parser           │
│ • Context Precision (AP Ranking)      │                                   │ • Exponential Backoff Retries         │
└───────────────────────────────────────┘                                   └───────────────────────────────────────┘
```

### Deterministic Metrics

1. **`Latency`**: Asserts that `trajectory.total_latency.seconds <= test_case.constraints["max_latency"]`. Prevents unacceptably slow agent loops.
2. **`TokenUsage`**: Asserts that total tokens consumed across all steps do not exceed `test_case.constraints["max_tokens"]`.
3. **`Cost`**: Evaluates financial expenditure in USD calculated per turn against `test_case.constraints["max_cost"]`.
4. **`ToolCalling`**: Validates three criteria:
   - All executed tool calls returned `success = True`.
   - All tool names defined in `test_case.expected_tool_calls` were executed.
   - Total tool calls do not exceed `test_case.constraints["max_tool_calls"]`.
5. **`ContextRecall`**: Measures the ratio of `ground_truth_context` items retrieved during execution.
6. **`ContextPrecision`**: Computes the Average Precision (AP) ranking score of retrieved context items to ensure the most relevant items are ranked highest.

### LLM-as-a-Judge Evaluators

1. **`Faithfulness`**: Evaluates whether every factual claim in the agent's response is directly supported by the retrieved context snippets without hallucinated additions.
2. **`Groundedness`**: Evaluates whether the response directly answers the user query while honoring all user constraints.
3. **`AnswerCorrectness`**: Compares the agent's output against the reference `expected_answer` for factual and semantic equivalence.
4. **`Hallucination`**: Safety evaluation that flags any fabricated facts or contradictions against ground truth.

#### Resilient Judge Output Parsing
LLM judges can be unreliable when instructed to produce JSON. EvalForge implements a two-tier parsing mechanism:
1. **Pydantic Structured Generation**: Requests schema-validated output via the provider SDK.
2. **Fallback Regex JSON Extraction**: If structured mode fails, the raw text response is inspected for code fences (````json ... ````) or outermost brackets (`{ ... }`), validated against `LLMJudgeOutputSchema`, and retried with exponential backoff.

### Deterministic vs. LLM Judge Comparison

| Evaluation Dimension | Deterministic Heuristic | LLM-as-a-Judge | Why Both Are Needed |
| :--- | :---: | :---: | :--- |
| **Tool Names & Schema** | **Strong** | Weak | Heuristics perform exact string and key matching instantaneously. |
| **Execution Latency** | **Strong** | Weak | Wall-clock execution is an exact programmatic measurement. |
| **USD Cost & Token Budgets** | **Strong** | Weak | Direct mathematical summation of token counters and pricing. |
| **Context Ranking (AP)** | **Strong** | Moderate | String-overlap ranking algorithms score retrieval ordering objectively. |
| **Semantic Correctness** | Limited | **Strong** | LLM judges evaluate semantic equivalence regardless of phrasing differences. |
| **Groundedness & Context Faithfulness** | Limited | **Strong** | LLM judges detect nuanced semantic hallucinations that keyword matchers miss. |
| **Hallucination Detection** | Limited | **Strong** | Cognitive evaluation detects fabricated claims not grounded in retrieved context. |

---

## 13. Golden Dataset Design

A **Golden Dataset** is a versioned collection of reference test scenarios (`GoldenTestCase`) designed to stress-test specific capabilities and failure modes of an agent.

```mermaid
flowchart LR
    subgraph GoldenDataset [GoldenDataset: travel_v1]
        Case001[GoldenTestCase 001: Flight Search]
        Case002[GoldenTestCase 002: Hotel Booking]
        Case003[GoldenTestCase 003: Policy Constraints]
    end

    subgraph TestCaseStructure [GoldenTestCase Attributes]
        Query[user_query: User Prompt]
        Context[ground_truth_context: Reference Snippets]
        ExpectedTools[expected_tool_calls: Required APIs]
        ExpectedAnswer[expected_answer: Reference Response]
        Constraints[constraints: max_latency, max_tokens, max_cost]
        ExpectedMetrics[expected_metrics & expected_judge_scores]
        Difficulty[difficulty & category & failure_mode]
    end

    Case001 --> TestCaseStructure
```

### Benchmark Suites Present in the Repository

EvalForge ships with 10 static, version-controlled JSON benchmarks in the [`datasets/`](file:///d:/AI/evalforge/datasets) directory:

| Dataset ID | Version | Cases | Primary Focus |
| :--- | :---: | :---: | :--- |
| **`travel_v1`** | `1.0.0` | 25 | Comprehensive baseline suite covering flight search, hotel booking, policy limits, and multi-turn itineraries. |
| **`travel_tool_calls`** | `1.0.0` | 15 | Multi-step tool chaining, dynamic argument formatting, and API parameter error recovery. |
| **`travel_regression`** | `1.0.0` | 10 | Standardized baseline suite for comparative regression testing across prompt and model iterations. |
| **`travel_safety`** | `1.0.0` | 10 | Stress-tests against instruction leaks, prompt injections, and corporate travel policy violations. |
| **`travel_adversarial`** | `1.0.0` | 10 | Unrealistic constraints, contradictory parameters, and ambiguous user queries. |
| **`travel_edge_cases`** | `1.0.0` | 12 | Leap years, time-zone boundary shifts, missing parameters, and currency conversion edge cases. |
| **`travel_long_context`** | `1.0.0` | 10 | Dense, multi-page context lookup inputs to evaluate context retrieval precision and recall. |
| **`travel_missing_context`** | `1.0.0` | 10 | Hallucination suppression when external search tools return empty observation sets. |
| **`travel_multilingual`** | `1.0.0` | 10 | Query processing, tool calling, and response grounding in non-English languages (Spanish, French, German). |
| **`travel_provider_benchmark`** | `1.0.0` | 10 | Standardized suite for comparative benchmarking across Gemini, Ollama, and OpenRouter models. |

---

## 14. Experiment and Regression Model

EvalForge groups evaluation runs under **Experiments** to provide historical delta comparisons and regression detection.

```
       Baseline Run (Run A)                                Candidate Run (Run B)
       SUT: v1.0.0 | Dataset: travel_v1                    SUT: v1.2.0 | Dataset: travel_v1
    ┌───────────────────────────────────┐               ┌───────────────────────────────────┐
    │  Success Rate:  92.0%             │               │  Success Rate:  96.0% (+4.0%)     │
    │  Avg Latency:   1.42s             │   ────────>   │  Avg Latency:   1.15s (-0.27s)    │
    │  Total Cost:    $0.0125           │    (Delta)    │  Total Cost:    $0.0098 (-$0.0027)│
    │  ContextRecall: 0.95              │               │  ContextRecall: 0.98  (+0.03)     │
    └───────────────────────────────────┘               └───────────────────────────────────┘
```

### Delta Calculation Engine
The `ExperimentEngine` treats the chronologically first run as the baseline ($R_0$) and calculates metric deltas for every subsequent candidate run ($R_i$):

$$\Delta \text{SuccessRate} = \text{SuccessRate}(R_i) - \text{SuccessRate}(R_0)$$
$$\Delta \text{Latency} = \text{AvgLatency}(R_i) - \text{AvgLatency}(R_0)$$
$$\Delta \text{Cost} = \text{TotalCost}(R_i) - \text{TotalCost}(R_0)$$
$$\Delta \text{Tokens} = \text{TotalTokens}(R_i) - \text{TotalTokens}(R_0)$$
$$\Delta \text{Metric}_k = \text{Score}_k(R_i) - \text{Score}_k(R_0)$$

The engine generates automated Markdown comparison tables highlighting regressions (negative success deltas, latency increases, or cost overruns) and identifies the top-performing SUT version.

---

## 15. Database Design

EvalForge uses an identical relational schema across PostgreSQL and SQLite, storing top-level metadata in indexed columns and complex nested structures in JSON fields:

```mermaid
erDiagram
    GOLDEN_DATASETS {
        TEXT dataset_id PK
        TEXT version PK
        TEXT name
        TEXT description
        TEXT test_cases "JSON array of GoldenTestCase"
        TEXT metadata "JSON object"
    }

    EVALUATION_RUNS {
        TEXT run_id PK
        TEXT dataset_id FK
        TEXT dataset_version
        TEXT sut_version
        TEXT timestamp "ISO-8601 string"
        TEXT cases "JSON array of TestCaseEvaluation"
        TEXT parameters "JSON object"
        TEXT summary "JSON object"
        TEXT metadata "JSON object"
    }

    EXPERIMENTS {
        TEXT experiment_id PK
        TEXT name
        TEXT description
        TEXT run_ids "JSON array of string run_ids"
        TEXT metadata "JSON object"
        TEXT created_at "ISO-8601 string"
    }

    GOLDEN_DATASETS ||--o{ EVALUATION_RUNS : "evaluated in"
    EXPERIMENTS ||--o{ EVALUATION_RUNS : "tracks"
```

### Database Schema Definition

#### `golden_datasets`
* `dataset_id` (`TEXT`): Unique dataset identifier.
* `version` (`TEXT`): Semantic version string (e.g., `1.0.0`).
* `name` (`TEXT`): Human-readable dataset name.
* `description` (`TEXT`): Dataset description and scope.
* `test_cases` (`TEXT`): Serialized JSON array of `GoldenTestCase` objects.
* `metadata` (`TEXT`): Serialized JSON dictionary of dataset metadata.
* **Primary Key**: `(dataset_id, version)`
* **Index**: `idx_datasets_id` on `(dataset_id)`

#### `evaluation_runs`
* `run_id` (`TEXT`): Unique run identifier (Primary Key).
* `dataset_id` (`TEXT`): ID of the evaluated dataset.
* `dataset_version` (`TEXT`): Version of the evaluated dataset.
* `sut_version` (`TEXT`): Version identifier of the agent SUT.
* `timestamp` (`TEXT`): ISO-8601 execution timestamp.
* `cases` (`TEXT`): Serialized JSON array of `TestCaseEvaluation` objects (trajectories, tool calls, and metric results).
* `parameters` (`TEXT`): Serialized JSON parameters (concurrency, retries, provider).
* `summary` (`TEXT`): Serialized JSON summary (success rate, avg latency, total tokens, total cost, avg metrics).
* `metadata` (`TEXT`): Arbitrary run metadata.
* **Index**: `idx_runs_dataset` on `(dataset_id)`

#### `experiments`
* `experiment_id` (`TEXT`): Unique experiment identifier (Primary Key).
* `name` (`TEXT`): Human-readable experiment name.
* `description` (`TEXT`): Experiment hypothesis and goal.
* `run_ids` (`TEXT`): Serialized JSON array of associated `run_id` strings.
* `metadata` (`TEXT`): Serialized JSON metadata.
* `created_at` (`TEXT`): ISO-8601 creation timestamp.

---

## 16. Persistence Strategy & SQLite / PostgreSQL Dual Support

EvalForge supports both SQLite and PostgreSQL via the `EvaluationRepository` interface:

* **Local Development / Testing**: Zero-configuration SQLite (`evalforge_platform.db`).
* **Staging / Production Deployments**: High-concurrency PostgreSQL.

### Connection Management and Transaction Safety
* **Thread-Safe Pooling**: `PostgresEvaluationRepository` manages connections using `psycopg2.pool.ThreadedConnectionPool(1, 20, dsn=database_url)` to prevent connection exhaustion during concurrent evaluation sweeps.
* **Context-Managed Transactions**: Database interactions use a custom context manager guaranteeing `conn.commit()` on success, `conn.rollback()` on exception, and automatic connection return via `pool.putconn(conn)` in a `finally` block.
* **Non-Blocking Async Offloading**: Synchronous database driver calls (`sqlite3`, `psycopg2`) are wrapped in `asyncio.to_thread` to prevent blocking the FastAPI asynchronous event loop.
* **Connection String Sanitization**: Startup hooks automatically convert cloud-injected `postgres://` prefixes (used by Render and Heroku) to `postgresql://` required by psycopg2.
* **Data Migration CLI Utility**: An ETL migration script (`scratch/migrate_sqlite_to_postgres.py`) allows migrating local SQLite records to PostgreSQL with automated table creation, upserts (`ON CONFLICT DO UPDATE`), and row-count verification.

---

## 17. Technology Stack

| Layer | Technology | Version / Spec | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `^3.11` | Core evaluation engine, data processing, and LLM integrations. |
| **API Framework** | FastAPI | `^0.110.0` | Asynchronous REST API, OpenAPI docs generation, and background task execution. |
| **ASGI Server** | Uvicorn | `^0.28.0` | High-performance asynchronous web server. |
| **Data Validation** | Pydantic | `^2.6.0` | Strict data validation, schema enforcement, and JSON serialization. |
| **Primary Database** | PostgreSQL | `15` | Production relational and JSON document persistence with connection pooling. |
| **Development DB** | SQLite | `3.x` | Zero-configuration local database engine. |
| **Database Driver** | Psycopg2-binary | `^2.9.9` | High-speed C-optimized PostgreSQL database adapter. |
| **HTTP Client** | HTTPX | `^0.26.0` | Asynchronous HTTP client for Ollama and external service communication. |
| **Frontend App** | Next.js / React | `14.x / 18.x` | Interactive evaluation dashboard, trajectory inspector, and metric visualization. |
| **Frontend Language**| TypeScript | `^5.3.3` | Compile-time type safety across UI components and API contracts. |
| **Data Fetching** | TanStack React Query | `^5.18.0` | Asynchronous state management, polling, and cache invalidation. |
| **Data Visualization**| Recharts | `^2.11.0` | Interactive charts for metric distributions and latency breakdowns. |
| **Styling** | Tailwind CSS | `^3.4.1` | Utility-first responsive styling and dark mode UI design. |
| **Icons** | Lucide React | `^0.330.0` | Production UI iconography. |
| **Containerization** | Docker / Compose | `Compose 3.8` | Reproducible multi-container local and deployment environments. |
| **Model Providers** | Gemini / Ollama / OpenRouter | SDK / REST | Model-agnostic LLM provider adapters for SUT and judge execution. |

---

## 18. Why Did We Choose This Tech Stack?

* **Python 3.11+**: The universal standard for AI/ML engineering, providing native SDKs for all major LLM providers (`google-generativeai`, `openai`, `httpx`) and high-performance typing support.
* **FastAPI**: Provides native async/await performance, automatic OpenAPI/Swagger documentation generation, strict Pydantic model validation, and seamless `BackgroundTasks` execution.
* **Pydantic v2**: Ensures rock-solid schema validation for complex, nested trajectory data and provides fast JSON serialization.
* **PostgreSQL 15**: Provides enterprise-grade reliability, concurrent write handling via connection pools, ACID guarantees, and efficient indexing for large JSON payload storage.
* **SQLite (Fallback)**: Enables instantaneous local development, unit testing, and offline benchmarking without spinning up database containers.
* **Next.js & TypeScript**: Enables building a responsive, component-driven dashboard with compile-time type validation ensuring frontend components match backend Pydantic API responses.
* **TanStack React Query**: Simplifies polling asynchronous benchmark runs, managing server state, and keeping trajectory traces responsive.
* **Pluggable LLM Adapters**: Decoupling the evaluation engine from proprietary SDKs allows teams to test local open-weights models via Ollama (zero API cost) or cloud models via Gemini and OpenRouter.

---

## 19. Key Architectural Decisions (ADRs)

1. **Clean Architecture & DDD Isolation**: Domain entities (`EvaluationRun`, `Trajectory`, `Step`, `GoldenDataset`) contain zero framework dependencies. Modifying FastAPI routes or switching databases requires zero changes to core evaluation logic.
2. **Provider & SUT Abstractions**: Decoupling through `AgentSUT` and `LLMProvider` protocols ensures that benchmark evaluation logic is completely agnostic to the agent implementation.
3. **Repository Pattern for Dual Storage**: Abstracting storage behind `EvaluationRepository` enables seamless portability between SQLite and PostgreSQL.
4. **Dual-Pronged Evaluation (Heuristics + Cognitive Judges)**: Deterministic checks enforce rigid operational boundaries (cost, latency, tool calls), while cognitive judges evaluate semantic alignment and groundedness.
5. **Trajectory-Level Observability**: Recording full intermediate steps (thoughts, tool calls, observations) enables diagnosing *why* an agent failed rather than simply recording that it did.
6. **Asynchronous Thread Offloading**: Relational database drivers (`psycopg2`, `sqlite3`) are synchronous; wrapping all database I/O in `asyncio.to_thread` preserves non-blocking API performance.

---

## 20. API Architecture

The FastAPI backend exposes RESTful endpoints with automatic Swagger documentation:

* **Swagger UI**: `/docs`
* **ReDoc Reference**: `/redoc`
* **OpenAPI Schema**: `/openapi.json`

### Endpoint Reference

| Method | Endpoint | Description | Request Body | Response Schema |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Verifies database connectivity and returns active DB engine. | None | `{"status": "healthy", "database": "postgresql", "timestamp": "..."}` |
| `GET` | `/api/datasets` | Lists all registered golden benchmark datasets. | None | `list[DatasetSummary]` |
| `POST` | `/api/datasets` | Registers a new Golden Dataset with schema validation. | `DatasetCreateSchema` | `{"status": "registered", "dataset_id": "...", "version": "..."}` |
| `GET` | `/api/datasets/{id}` | Retrieves the latest version of a dataset. | None | `GoldenDataset` |
| `GET` | `/api/datasets/{id}/versions/{v}` | Retrieves a specific version of a dataset. | None | `GoldenDataset` |
| `POST` | `/api/benchmarks/run` | Triggers an evaluation run asynchronously via background tasks. | `RunBenchmarkRequestSchema` | `{"status": "running", "run_id": "run-..."}` |
| `GET` | `/api/runs` | Lists historical benchmark runs with summary metrics. | None | `list[RunSummary]` |
| `GET` | `/api/runs/{run_id}` | Retrieves complete evaluation run data including full trajectories. | None | `EvaluationRun` (Formatted with metric lists) |
| `GET` | `/api/runs/{run_id}/report` | Generates a structured Markdown evaluation report. | None | `{"run_id": "...", "report_markdown": "..."}` |
| `GET` | `/api/experiments` | Lists registered experiments. | None | `list[ExperimentSummary]` |
| `POST` | `/api/experiments` | Creates a new evaluation experiment. | `ExperimentCreateSchema` | `{"status": "created", "experiment_id": "..."}` |
| `GET` | `/api/experiments/{id}` | Retrieves experiment details, run list, and delta report. | None | `ExperimentDetails` |
| `POST` | `/api/experiments/{id}/runs/{run_id}` | Associates an evaluation run with an experiment. | None | `{"status": "added", "experiment_id": "...", "run_id": "..."}` |

---

## 21. Frontend Architecture

The Next.js 14 frontend provides a reactive dashboard for inspecting benchmarks, evaluating runs, and comparing experiments:

```mermaid
flowchart TD
    subgraph FrontendApp [Next.js App Router]
        Page[app/page.tsx - Main Tab Controller]
        Overview[components/dashboard/OverviewTab.tsx]
        Datasets[components/datasets/DatasetsTab.tsx]
        Runs[components/runs/RunsTab.tsx]
        TraceInspector[components/runs/TrajectoryInspector.tsx]
        Experiments[components/experiments/ExperimentsTab.tsx]
    end

    subgraph StateManagement [Data Fetching & Cache]
        ReactQuery[TanStack React Query Hooks]
        APIService[services/api.ts]
    end

    subgraph Visualizations [Data Visualization]
        Charts[Recharts: Metric Distributions & Latency]
        Icons[Lucide Icons]
        Markdown[React Markdown / GFM]
    end

    Page --> Overview
    Page --> Datasets
    Page --> Runs
    Page --> Experiments
    Runs --> TraceInspector
    Overview --> ReactQuery
    Datasets --> ReactQuery
    Runs --> ReactQuery
    Experiments --> ReactQuery
    ReactQuery --> APIService
    Overview --> Charts
    TraceInspector --> Markdown
```

### Dashboard Panels
1. **Overview Tab**: Real-time launchpad for executing benchmark sweeps, configuring concurrency and retries, and monitoring platform health.
2. **Datasets Tab**: Interactive explorer for inspecting benchmark test cases, difficulty categories, expected tool sequences, ground-truth context, and constraint thresholds.
3. **Run History & Trajectory Inspector**: Audit past benchmark runs with aggregated pass/fail statistics, latency cards, and a step-by-step trace viewer detailing thoughts, tool arguments, observations, and judge justifications.
4. **Experiments Tab**: Multi-run delta comparator highlighting performance improvements or regressions across SUT versions.

---

## 22. Production Deployment Architecture

EvalForge is designed for cloud deployment using decoupled compute and managed persistence:

```mermaid
flowchart LR
    User[Developer / Browser] -->|HTTPS| Vercel[Vercel Cloud - Next.js Frontend]
    Vercel -->|REST API Requests / CORS| Render[Render Web Service - FastAPI Backend]
    Render -->|Threaded Connection Pool| Postgres[(Render Managed PostgreSQL 15)]
    Render -->|API Calls / HTTPS| Gemini[Google Gemini API]
    Render -->|API Calls / Local| Ollama[Local Ollama Server]
    Render -->|API Calls / HTTPS| OpenRouter[OpenRouter API]
```

* **Frontend**: Hosted on **Vercel** with automatic preview deployments and environment configuration (`NEXT_PUBLIC_API_URL`).
* **Backend**: Containerized **FastAPI** service running on **Render** (via Dockerfile).
* **Database**: Managed **PostgreSQL 15** on Render with SSL enforcement and connection pooling.
* **CORS Security**: Backend `CORSMiddleware` configured to whitelist Vercel deployment domains via `ALLOWED_ORIGINS`.

---

## 23. Security and Reliability

* **Secret Governance**: All API keys (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`) and database credentials (`DATABASE_URL`) are loaded from environment variables and strictly excluded from version control.
* **CORS Origin Whitelisting**: The API explicitly restricts cross-origin resource sharing to specified production frontend origins.
* **Connection Pool Protection**: The PostgreSQL adapter uses `ThreadedConnectionPool` (1-20 connections) to prevent server connection exhaustion under high benchmark concurrency.
* **Transaction Rollback Guarantees**: Database operations are wrapped in context managers with automatic rollback on failure to maintain database consistency.
* **Strict Payload Validation**: All incoming requests are validated against Pydantic schemas before reaching use-case handlers.
* **LLM Judge Resiliency**: LLM judge executions incorporate automatic retry logic with exponential backoff and text-extraction fallbacks to handle transient rate limits or malformed model responses.

---

## 24. Testing Strategy

EvalForge maintains comprehensive unit and integration test suites:

```
tests/
├── unit/
│   ├── test_domain_models.py       # Validates Pydantic entities, value objects, and immutability
│   ├── test_benchmark_config.py    # Tests benchmark execution configs and retry policies
│   ├── test_benchmark_runner.py    # Tests concurrency bounding and trajectory evaluation
│   ├── test_evaluators.py          # Verifies deterministic metrics (latency, cost, tokens, context)
│   ├── test_judge_engine.py        # Tests LLM judge execution, prompt rendering, and fallback parsing
│   ├── test_metric_registry.py     # Tests metric registration and duplicate prevention
│   ├── test_dataset_engine.py      # Tests dataset loading, schema mapping, and validation
│   ├── test_experiment_engine.py   # Tests multi-run delta calculations and markdown summaries
│   ├── test_providers.py           # Verifies LLM provider mock modes and generation contracts
│   ├── test_sqlite_repository.py   # Tests SQLite CRUD operations and index lookups
│   ├── test_travel_agent_sut.py    # Verifies reference SUT execution and tool simulations
│   └── test_travel_services.py     # Tests mock travel API services (flights, hotels, weather)
└── integration/
    ├── test_api.py                 # Tests FastAPI routes, dataset registration, and background tasks
    ├── test_e2e_evaluation.py      # Tests complete end-to-end benchmark execution workflows
    └── test_postgres_repository.py # Tests PostgreSQL connection pooling, upserts, and concurrency
```

### Automated CI Workflow
Every push and pull request runs through GitHub Actions ([`.github/workflows/ci.yml`](file:///d:/AI/evalforge/.github/workflows/ci.yml)):
1. **Formatting Check**: `black --check src tests`
2. **Linting Check**: `ruff check src tests`
3. **Static Type Analysis**: `mypy src tests`
4. **Test Suite Execution**: `pytest`

---

## 25. Project Structure

```
evalforge/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Continuous integration workflow (Black, Ruff, Mypy, Pytest)
├── datasets/                          # 10 version-controlled Golden Benchmark Suites (JSON)
│   ├── travel_v1.json                 # Baseline evaluation benchmark (25 cases)
│   ├── travel_tool_calls.json         # Tool chaining and dynamic argument benchmark
│   ├── travel_regression.json         # Regression baseline dataset
│   ├── travel_safety.json             # Policy compliance and safety benchmark
│   ├── travel_adversarial.json        # Contradictory constraints benchmark
│   ├── travel_edge_cases.json         # Date, timezone, and currency edge cases
│   ├── travel_long_context.json       # Dense context retrieval benchmark
│   ├── travel_missing_context.json    # Hallucination suppression benchmark
│   ├── travel_multilingual.json       # Multi-language agent query benchmark
│   └── travel_provider_benchmark.json # Cross-model evaluation suite
├── docs/                              # Architecture documentation & ADRs
│   ├── adr/                           # Architectural Decision Records (0001 - 0006)
│   └── architecture.md                # System architecture documentation
├── examples/                          # Reference System Under Test (SUT) implementations
│   └── travel_agent/
│       ├── services.py                # Simulated external tools (Flights, Hotels, Weather, Policies)
│       └── travel_agent_sut.py        # Reference Travel Agent SUT implementing AgentSUT
├── frontend/                          # Next.js 14 React Dashboard (TypeScript)
│   ├── src/
│   │   ├── app/                       # Next.js App Router (layout, page)
│   │   ├── components/                # Modular UI components (Dashboard, Datasets, Runs, Experiments)
│   │   ├── hooks/                     # Custom React Query data-fetching hooks
│   │   ├── services/                  # Backend REST API client
│   │   └── types/                     # TypeScript data contracts matching Pydantic schemas
│   ├── package.json                   # Frontend dependencies and build scripts
│   └── Dockerfile                     # Frontend production Dockerfile
├── src/                               # Python Backend (Clean Architecture)
│   ├── domain/                        # Pure domain models, entities, and interfaces
│   │   ├── entities/                  # GoldenDataset, EvaluationRun, Trajectory, Step, ToolCall, Experiment
│   │   ├── interfaces/                # EvaluationRepository, BaseEvaluator, AgentSUT, LLMProvider
│   │   └── value_objects/             # TokenUsage, Cost, Latency value objects
│   ├── use_cases/                     # Core evaluation business logic
│   │   ├── datasets/                  # Dataset loaders, validators, and registries
│   │   ├── experiments/               # ExperimentEngine and delta calculation logic
│   │   ├── judges/                    # LLMJudgeEngine, prompt templates, and cognitive rubrics
│   │   ├── metrics/                   # Deterministic evaluators, MetricRegistry, and AggregationEngine
│   │   ├── reporting/                 # Markdown report generation utilities
│   │   └── runners/                   # BenchmarkRunner bounded concurrency orchestrator
│   ├── adapters/                      # Secondary adapters (Databases, API, LLM Providers)
│   │   ├── api/                       # FastAPI controllers, schemas, and middleware (app.py)
│   │   ├── llm/                       # GeminiProvider, OllamaProvider, OpenRouterProvider
│   │   └── repositories/              # PostgresEvaluationRepository, SqliteEvaluationRepository
│   └── infrastructure/                # Structured logging and configuration
├── tests/                             # Automated test suite
│   ├── unit/                          # 14 unit test suites covering domain models, evaluators, and engines
│   └── integration/                   # 3 integration test suites covering API, E2E flow, and PostgreSQL
├── .env.example                       # Environment variable configuration template
├── Dockerfile                         # Backend production Dockerfile
├── docker-compose.yml                 # Multi-service composition (PostgreSQL, Backend, Frontend)
├── pyproject.toml                     # Poetry project configuration & tool settings
├── requirements.txt                   # Production and development Python dependencies
└── README.md                          # Production engineering documentation
```

---

## 26. Local Development Setup

### Prerequisites
* **Python**: `3.11+`
* **Node.js**: `18+` (npm `9+`)
* **Docker & Docker Compose** (optional, for local PostgreSQL service)

### 1. Backend Setup

Clone the repository and create a Python virtual environment:

```bash
git clone https://github.com/jacobjerryarackal/evalforge.git
cd evalforge

# Create and activate virtual environment
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

Create a root `.env` configuration file:

```bash
cp .env.example .env
```

Configure your environment variables in `.env`:

```env
# LLM Provider Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
OLLAMA_API_BASE=http://localhost:11434

# Database Connection (Leave blank or omit to use local SQLite: evalforge_platform.db)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/evalforge

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000
```

Start the FastAPI backend server:

```bash
python -m uvicorn src.adapters.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be accessible at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 2. Frontend Setup

In a new terminal, navigate to the `frontend/` directory and install dependencies:

```bash
cd frontend
npm install
```

Start the Next.js development server:

```bash
npm run dev
```

The UI will be accessible at `http://localhost:3000`.

### 3. Running with Docker Compose

To spin up the entire stack (PostgreSQL database, FastAPI backend, and Next.js frontend) in isolated containers:

```bash
docker-compose up --build
```

Services will be exposed on:
* **Frontend**: `http://localhost:3000`
* **Backend API**: `http://localhost:8000`
* **PostgreSQL**: `localhost:5432`

---

## 27. Running Tests and Code Quality

Run the full verification suite locally:

```bash
# 1. Code Formatting Check
black --check src tests

# 2. Code Linting Check
ruff check src tests

# 3. Static Type Analysis
mypy src tests

# 4. Execute Full Pytest Suite
pytest -v
```

---

## 28. Example Evaluation Workflow

The walkthrough below demonstrates how a test case progresses through evaluation:

### 1. Test Scenario (`GoldenTestCase`)
```json
{
  "id": "case-001",
  "category": "flight_search",
  "user_query": "Book a one-way flight from NYC to London under $500 for tomorrow.",
  "expected_tool_calls": ["search_flights", "check_booking_policy"],
  "ground_truth_context": ["Flight BA178 departs JFK to LHR at 08:30 for $420."],
  "expected_answer": "Flight BA178 from NYC to London has been identified for $420.",
  "latency_constraint": 3.0,
  "token_constraint": 1500,
  "cost_constraint": 0.02
}
```

### 2. SUT Execution & Trajectory Capture
The agent SUT executes 2 reasoning steps:
* **Step 1**: Reasoning: *"Searching flights from NYC to LHR"* $\rightarrow$ Invokes `search_flights(origin="NYC", destination="LHR")` $\rightarrow$ Observation: `[{"flight": "BA178", "price": 420}]`.
* **Step 2**: Reasoning: *"Validating budget constraint"* $\rightarrow$ Invokes `check_booking_policy(amount=420, max_budget=500)` $\rightarrow$ Observation: `"Approved"`.
* **Final Response**: *"Flight BA178 from NYC to London is available for $420."*
* **Telemetry**: Latency = `1.24s`, Tokens = `380`, Cost = `$0.0019`.

### 3. Metric & Judge Scoring
* `LatencyEvaluator`: `1.24s <= 3.0s` $\rightarrow$ **1.0 (PASS)**
* `TokenUsageEvaluator`: `380 <= 1500` $\rightarrow$ **1.0 (PASS)**
* `CostEvaluator`: `$0.0019 <= $0.02` $\rightarrow$ **1.0 (PASS)**
* `ToolCallingEvaluator`: `search_flights` and `check_booking_policy` called successfully $\rightarrow$ **1.0 (PASS)**
* `ContextRecallEvaluator`: Ground truth string matched in retrieved context $\rightarrow$ **1.0 (PASS)**
* `Faithfulness` (LLM Judge): Response contains no hallucinated flight numbers $\rightarrow$ **Score: 1.0 (Confidence: 0.95)**
* `Groundedness` (LLM Judge): Output directly answers user query $\rightarrow$ **Score: 1.0 (Confidence: 1.0)**

### 4. Persistence & Regression Delta
The complete `TestCaseEvaluation` is appended to `EvaluationRun(run_id="run-a0aa7aa3")`, persisted to PostgreSQL, and compared against the baseline run in the experiment to produce performance deltas.

---

## 29. Limitations

* **Stochastic Variance in LLM Judges**: Cognitive evaluators relying on LLMs are subject to subtle non-determinism despite `temperature=0.0`.
* **In-Process Task Execution**: Benchmark runs are currently executed via FastAPI `BackgroundTasks`. While concurrency is bounded via `asyncio.Semaphore`, high-volume enterprise evaluation sweeps would benefit from a distributed worker queue (e.g., Celery or Redis Workers).
* **Static Model Pricing Tables**: Token cost calculations use fixed price per 1k tokens constants; dynamic pricing API sync is not yet implemented.
* **Context Overlap Heuristic**: Deterministic context recall uses substring matching heuristics which may under-score paraphrased retrieved context compared to semantic embeddings.

---

## 30. Planned / Future Work

The following enhancements are planned for future releases:

* [ ] **Distributed Task Queue**: Offloading benchmark sweeps to distributed Celery / Redis worker clusters for large-scale enterprise execution.
* [ ] **Live WebSocket / SSE Trajectory Streaming**: Real-time step-by-step streaming of intermediate thoughts and tool calls to the frontend UI as the agent executes.
* [ ] **Multi-Agent Interaction Tracing**: Observability graphs capturing interactions, delegation chains, and consensus across multi-agent swarms.
* [ ] **Automated CI/CD PR Evaluation Gates**: A GitHub Action / CLI command that runs evaluation sweeps on PRs and blocks merges if regression deltas exceed predefined thresholds.
* [ ] **Authentication & RBAC**: Integration of OAuth2 / JWT authentication and Role-Based Access Control to manage multi-tenant evaluation workspaces.

---

## 31. Engineering Lessons Demonstrated

This project demonstrates practical software engineering patterns for AI systems:
1. **Clean Architecture & DDD**: Strict isolation of business logic from infrastructure and UI frameworks.
2. **Observability over Assertions**: Moving beyond pass/fail assertions to capture multi-turn reasoning trajectories.
3. **Database Portability**: Using the Repository Pattern to support zero-config SQLite and connection-pooled PostgreSQL side-by-side.
4. **Resilient LLM Output Handling**: Implementing multi-tier structured generation with regex extraction fallbacks and exponential backoff retry policies.
5. **Async Runtime Discipline**: Offloading synchronous relational database operations via `asyncio.to_thread` to prevent event loop starvation.
6. **Empirical Regression Analysis**: Treating AI agent quality as a quantitative measurement problem backed by versioned benchmarks and automated delta tracking.

---

## 32. License

This project is open-source software licensed under the [MIT License](LICENSE).
