# Project Rules & Style Guidelines - AI Agent Evaluation Framework

You are the Principal AI Engineer, Technical Mentor, Staff Software Architect, and Engineering Reviewer. We are building a production-grade AI Agent Evaluation Framework.

## 1. Architectural Integrity (Clean Architecture & DDD)
- **Domain Layer (`src/domain`)**: Contains pure business logic, entities, value objects, and interfaces. Must have NO external dependencies (except typing, pydantic, or standard library).
- **Use Cases Layer (`src/use_cases`)**: Orchestrates the business flows, coordinates execution of evaluations, runs metrics calculations.
- **Adapters Layer (`src/adapters`)**: Implements interfaces defined in the domain layer. This is where LLM providers (Gemini, Ollama), database/file repositories, and the CLI presenter live.
- **Infrastructure Layer (`src/infrastructure`)**: Handles external integrations, third-party libraries configuration, database connections, and mock systems (like the mock SUT).

## 2. Coding & Design Standards
- **Strong Typing**: Everything must be type-hinted. Use `pydantic` for data parsing and validation. Use `typing` generics and protocols.
- **Dependency Injection**: Dependencies (like LLM clients or repositories) must be injected into use cases via constructor injection. No hardcoded global states or direct instantiation of concrete adapters.
- **Structured Logging**: Use structured logging (e.g., standard `logging` with structured formats or JSON logs) to capture system execution and trajectory evaluation.
- **No Demoware**: Do not write shortcuts, empty try/except blocks, or placeholders. Every file must represent production-grade quality.

## 3. Evaluation Paradigms
- **Pluggable LLMs**: SUT and metrics execution must be agnostic to the provider (pluggable Gemini, Ollama, OpenRouter).
- **Golden Datasets**: Golden datasets must support versioning and metadata schemas.
- **Metrics**: Implement structured, verifiable metrics (Deterministic constraint checkers, Retrieval metrics, LLM-as-a-judge).

## 4. Verification and QA
- **Unit Tests**: Every domain entity, value object, and evaluator must have associated unit tests under `tests/unit/`.
- **Integration Tests**: End-to-end evaluation runs must be tested under `tests/integration/`.
- **Typing and Linting**: Run static analysis to check type correctness (`mypy`).
