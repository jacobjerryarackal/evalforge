# AI Agent Evaluation Framework (Booking.com 2026 Inspired)

This repository contains a production-grade AI Agent Evaluation Framework designed to benchmark, audit, and observe AI agents running on travel and accommodation platforms.

---

## 🛠️ Engineering Operating System (EOS)

The repository's development guidelines, roadmaps, and designs are managed through the following documents:

- 📖 **[ENGINEERING_PLAYBOOK.md](file:///d:/AI/evalforge/ENGINEERING_PLAYBOOK.md)**: Permanent handbook for engineering workflows (Design Template, GStack, Agentic SWE, Genesis Kit).
- 🧠 **[PROJECT_KNOWLEDGE.md](file:///d:/AI/evalforge/PROJECT_KNOWLEDGE.md)**: Project's long-term memory containing vision, architectural patterns, and known limitations.
- 💻 **[TECH_STACK.md](file:///d:/AI/evalforge/TECH_STACK.md)**: Details and justifications of all technologies selected.
- 🎯 **[PROJECT_MASTER_PLAN.md](file:///d:/AI/evalforge/PROJECT_MASTER_PLAN.md)**: Core planning document specifying deliverables, definition of done, and verification for each sprint.
- 📈 **[ROADMAP.md](file:///d:/AI/evalforge/ROADMAP.md)**: Compressed 1-week execution schedule.
- 🚦 **[PROJECT_STATE.md](file:///d:/AI/evalforge/PROJECT_STATE.md)**: Tracks active state, risks, ADR index, and completion %.

---

## 🚀 Key Features
- **Domain Agnostic Core**: Core execution and benchmarking engines are entirely domain-independent.
- **Reference Implementation**: Includes a simulated travel agent assistant ([examples/travel_agent](file:///d:/AI/evalforge/examples/travel_agent)) demonstrating E2E agent evaluation.
- **Pluggable Providers**: Fully decoupled LLM interface supporting Gemini, Ollama, and OpenRouter.
- **Clean Architecture**: Decoupled domain model, strict use-case orchestrators, interchangeable adapters, and modular infrastructure.
- **Comprehensive Metrics**:
  - *Retrieval*: Context Precision, Context Recall.
  - *Correctness*: Groundedness, Faithfulness, Answer Correctness.
  - *Agent Trajectory*: Step loop tracking, Tool execution error rates.
  - *Performance*: Cost, Latency, Token usage profiling.
  - *Policy & Safety*: Instruction-following, prompt injection prevention.

## 📂 Repository Structure
```
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   └── architecture.md         # Overall architectural blueprint
├── examples/
│   └── travel_agent/           # Reference Implementation (SUT & Simulation)
│       ├── services.py         # Mock flight/hotel/weather catalog services
│       └── travel_agent_sut.py # Mock travel assistant agent SUT
├── src/
│   ├── domain/                 # Core Entities, Value Objects & interfaces
│   │   ├── entities/           # Trajectory, Step, Dataset, EvaluationRun
│   │   ├── value_objects/      # TokenUsage, Cost, Latency
│   │   └── interfaces/         # Contracts for LLM, Repositories, Evaluators
│   ├── use_cases/              # Evaluation logic & metric calculators
│   ├── adapters/               # Concrete integrations (Gemini, Sqlite)
│   └── infrastructure/         # Global environment & config infrastructure
├── tests/
│   ├── unit/                   # Unit tests (Domain objects, rules validation)
│   └── integration/            # Multi-component flow validations
└── pyproject.toml              # Project packaging & dependencies
```

## 🛠️ Getting Started

### Prerequisites
- Python 3.11+
- Virtual environment (`.venv`)

### Installation
Activate your virtual environment and install dependencies:
```bash
# Windows
.venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
Execute the unit and integration tests using `pytest`:
```bash
# From the root directory
pytest
```
