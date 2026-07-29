# ADR-0002: Tech Stack and Architectural Patterns

## Status
Approved

## Context
We need to design a solid, modular structure that accommodates complex agent evaluations (trajectory parsing, retrieval evaluation, LLM-as-a-judge scoring) while maintaining strict provider independence and allowing clean testing.

## Decision
We make the following technical decisions:
1. **Language**: Python 3.11.9
   - *Why*: Strongest ecosystem for data analysis (Pandas/Polars), async network calls (Httpx), validation (Pydantic), and LLM/NLP tooling.
2. **Architecture**: Clean Architecture combined with Domain-Driven Design (DDD) principles
   - *Why*: Decouples the business rules (what defines an evaluation and its metrics) from infrastructure details (LLM SDKs, SQLite, CLI output).
   - *Layers*:
     - **Domain**: Pure domain models (`EvaluationRun`, `Trajectory`, `MetricResult`) and interfaces (`LLMProvider`, `Repository`). No external library dependencies.
     - **Use Cases**: Contains orchestration logic (`BenchmarkRunner`, `FaithfulnessEvaluator`).
     - **Adapters**: Concrete implementations of domain interfaces (`GeminiProvider`, `SqliteRepository`, `ConsolePresenter`).
     - **Infrastructure**: Configs, SUT Mock wrappers, dependency-injection wiring.
3. **Data Validation**: Pydantic v2
   - *Why*: Type safety, high performance (written in Rust), and clean model declaration for nested configurations and trajectories.
4. **Data Persistence**: Repository Pattern with File/SQLite implementation
   - *Why*: Allows us to start quickly with local file storage (JSON or SQLite) while guaranteeing that the interface can easily swap to Postgres or a document DB later without modifying the Use Case or Domain layers.
5. **Package Management**: Virtual environment (`.venv`) with standard `pip` and a `pyproject.toml` definition.
   - *Why*: Poetry is preferred but not globally available. Running inside a standard `.venv` with `pyproject.toml` is highly portable and ensures we don't pollute the global scope.

## Consequences
- **Positive**:
  - Code is highly unit-testable because we can easily mock adapters (e.g. testing Use Cases with a Mock Repository and Mock LLM).
  - Clear code organization (prevents "spaghetti code" common in AI scripts).
  - Changing evaluation databases or LLM providers requires adding a new class in the Adapters layer, leaving existing logic untouched (SOLID Open-Closed Principle).
- **Negative**:
  - More files and directories to create and maintain.
  - Minor translation overhead when mapping domain objects to database models.
