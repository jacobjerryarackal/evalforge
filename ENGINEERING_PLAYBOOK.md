# ENGINEERING_PLAYBOOK — EvalForge

This document is the permanent engineering handbook for **EvalForge**. It defines the unified software engineering workflow that every sprint must execute. This workflow synthesizes the principles of Clean Architecture, GStack review pipelines, Genesis documentation habits, and Agentic SWE lifecycles.

---

## 1. The Unified Engineering Workflow

Every Engineering Sprint must proceed through these 9 sequential stages. No stage may be skipped.

```
 [Design] ──> [Arch Review] ──> [Implement] ──> [Unit Test] ──> [Static Checks]
                                                                      │
 [Done & Stop] <── [Gate & State] <── [Interview Notes] <── [Docs] <──┘
```

---

### Stage 1: Design (Workflow & Failures)
Before writing code:
- **Map Actor Workflow**: Identify trigger inputs, system boundaries, model components, and human checkpoints.
- **Conduct Failure Mode Analysis**: List all ways the agentic system under test (SUT) or LLM adapters could fail (API rates, timeouts, tool looping, hallucinations) and define how the platform will capture or isolate them.
- **Define Sprint Scope**: Lock down exactly what is being implemented.

### Stage 2: Architecture Review
Validate code plans against Clean Architecture & SOLID design principles:
- **Dependency Flow Check**: Ensure dependencies point inward (Domain is pure; Use Cases contain business logic; Adapters contain third-party SDKs like Google Generative AI).
- **Dependency Inversion (DIP)**: Concrete adapters must implement Domain-defined interfaces.
- **Liskov Substitution**: Abstract base classes (e.g., `BaseEvaluator`) must be substitutable by their implementations.

### Stage 3: Implementation
Write production-grade code:
- **Strong Typing**: Use type hints everywhere. Validate nested data and configurations with `pydantic`.
- **Constructor Injection**: Inject all adapter dependencies (LLMs, database repos) via class constructors. No hardcoded global configurations.
- **No Demoware**: Handle exceptions, trace failures, and use Python's `logging` module for structured outputs. No empty try-except blocks.

### Stage 4: Testing (Unit & Integration)
- **Unit Tests**: Place in `tests/unit/`. Unit tests must run locally, be fast, and use mock interfaces (e.g., `InMemoryEvaluationRepository` or `MockAgentSUT`) rather than real external network requests.
- **Integration Tests**: Place in `tests/integration/`. Test actual API requests and database transactions (e.g. SQLite database writes) to ensure integration health.

### Stage 5: Quality & Static Checks
Confirm the code passes style and compilation checks:
- **Formatter**: Run `black` to standardize spacing and code wrapping.
- **Linter**: Run `ruff` to ensure compliance with Python formatting guidelines.
- **Type Checker**: Run `mypy` to verify complete static type correctness.

### Stage 6: Documentation
- **Architecture Updates**: Document class and flow diagrams in `docs/architecture.md`.
- **ADRs**: Document significant architectural decisions in sequential records under `docs/adr/`.
- **Markdown Links**: Create clickable relative links for all classes and files mentioned in docs (e.g., `[AgentSUT](file:///path/to/sut.py)`).

### Stage 7: Interview Prep Notes
Prepare for technical interviews by documenting:
- **The Why**: Explain why the chosen design exists.
- **The Alternatives**: Compare the choice against other solutions.
- **Production considerations**: Detail scale, performance, billing, and latency impacts.
- **Beginner Mistakes**: List common anti-patterns and how we avoided them.
- **Real-world Examples**: Link the concepts to how leading tech companies (Booking.com, Airbnb) build them.

### Stage 8: Engineering Gate
Evaluate the **Definition of Done (DoD)**:
- Do 100% of unit tests pass?
- Does mypy compile with zero errors?
- Are all environment variables and secrets isolated?
- If yes, proceed. If no, fix violations before completing the sprint.

### Stage 9: Project State Update
Update [PROJECT_STATE.md](file:///d:/AI/AI%20Agent%20Evaluation%20Framework/PROJECT_STATE.md):
- Mark the current sprint as completed.
- Log new ADRs in the index.
- Calculate and update the total completion percentage.
- Define the starting scope for the next sprint.
- **STOP**. Never execute the next sprint automatically. Wait for approval.
