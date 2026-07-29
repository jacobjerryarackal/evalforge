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
