# ENGINEERING_PLAYBOOK — EvalForge

This document is the permanent engineering handbook for **EvalForge**. It defines the unified software engineering workflow that every sprint must execute. This workflow synthesizes the principles of **Clean Architecture / GStack**, **Design Template**, **Agentic SWE Kit**, and **Genesis Kit** methodologies into a single, permanent engineering pipeline. No stages may be skipped.

---

## 1. Permanent Engineering Workflow

Every Engineering Sprint must proceed through these 9 sequential stages.

```
 [Design (Design Template)] ──> [Arch Review (GStack)] ──> [Implement (Agentic SWE/GStack)]
                                                                        │
 [Done & Stop] <── [Gate & State (Genesis)] <── [Interview Notes (Genesis)] <── [Tests/Checks (GStack)]
```

---

### Stage 1: Design (Design Template)
Before writing any code, establish structural boundaries:
- **Map Actor Workflow**: Identify trigger inputs, system boundaries, model components, and human checkpoints. Map out how the SUT (System Under Test) and the Runner will communicate.
- **Conduct Failure Mode Analysis**: List all ways the agentic system or LLM adapters could fail (API rate limits, timeout exceptions, tool loop crashes, structural hallucinations) and define how the platform will capture and isolate them.
- **Define Sprint Scope**: Lock down exactly what is being implemented, avoiding scope creep.

### Stage 2: Architecture Review (GStack)
Validate code plans against Clean Architecture & SOLID design principles:
- **Dependency Flow Check**: Ensure dependencies point inward (Domain is pure; Use Cases contain business logic; Adapters contain third-party SDKs like Google Generative AI).
- **Dependency Inversion (DIP)**: Concrete adapters must implement Domain-defined interfaces. Use case orchestrators should depend only on Domain contracts (interfaces), never on concrete adapters.
- **Liskov Substitution**: Abstract base classes (e.g., `BaseEvaluator`) must be substitutable by their implementations.

### Stage 3: Implementation (Agentic SWE Kit & GStack)
Write production-grade code:
- **Strong Typing**: Use type hints everywhere. Validate nested data and configurations with `pydantic`.
- **Constructor Injection**: Inject all adapter dependencies (LLMs, database repositories) via class constructors. No hardcoded global configurations or inline instantiation of adapters.
- **Agentic Safeguards**: Implement structured exception handling, request retry policies with backoff, and execution guards (e.g. step counters, tool-call syntax checks, token budgets) to prevent infinite agent loops and excessive costs.
- **No Demoware**: Handle exceptions, trace failures, and use Python's standard `logging` module for structured logging. No empty try-except blocks or placeholder stubs.

### Stage 4: Testing (GStack & Agentic SWE Kit)
Verify correctness at all levels:
- **Unit Tests**: Place in `tests/unit/`. Unit tests must run locally, be fast, and use mock interfaces (e.g., `InMemoryEvaluationRepository` or `MockAgentSUT`) rather than real external network requests.
- **Integration Tests**: Place in `tests/integration/`. Test actual API requests and database transactions (e.g. SQLite database writes) to ensure integration health.

### Stage 5: Quality & Static Checks (GStack)
Confirm the code passes style and compilation checks:
- **Formatter**: Run `black` to standardize spacing and code wrapping.
- **Linter**: Run `ruff` to ensure compliance with Python formatting guidelines.
- **Type Checker**: Run `mypy` to verify complete static type correctness.

### Stage 6: Documentation (Genesis Kit)
Capture context for long-term memory:
- **Architecture Updates**: Document class and flow diagrams in `docs/architecture.md`.
- **ADRs**: Document significant architectural decisions in sequential records under `docs/adr/`.
- **Markdown Links**: Create clickable relative links for all classes and files mentioned in docs (e.g., `[AgentSUT](file:///d:/AI/evalforge/src/domain/interfaces/sut.py)`).
- **Long-Term Memory**: Keep [PROJECT_KNOWLEDGE.md](file:///d:/AI/evalforge/PROJECT_KNOWLEDGE.md) updated with key insights, assumptions, and known limitations.

### Stage 7: Interview Prep Notes (Genesis Kit / Mentorship)
Prepare for technical interviews by documenting:
- **The Why**: Explain why the chosen design exists and what trade-offs were made.
- **The Alternatives**: Compare the choice against other solutions.
- **Production Considerations**: Detail scale, performance, billing, and latency impacts.
- **Beginner Mistakes**: List common anti-patterns and how we avoided them.
- **Real-world Examples**: Link the concepts to how leading tech companies (Booking.com, Airbnb) build them.

### Stage 8: Engineering Gate (GStack & DoD)
Evaluate the **Definition of Done (DoD)**:
- Do 100% of unit tests pass?
- Does mypy compile with zero errors?
- Are all environment variables and secrets isolated?
- If yes, proceed. If no, fix violations before completing the sprint.

### Stage 9: Project State Update (Genesis Kit)
Update [PROJECT_STATE.md](file:///d:/AI/evalforge/PROJECT_STATE.md):
- Mark the current sprint as completed.
- Log new ADRs in the index.
- Calculate and update the total completion percentage.
- Define the starting scope for the next sprint.
- **STOP**. Never execute the next sprint automatically. Wait for approval.
