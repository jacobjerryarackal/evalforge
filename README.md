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
- **LLM Judge Engine**: Reusable, extensible execution engine for qualitative LLM Judges, supporting Pydantic structured output validation, text fallback manual JSON extraction, confidence validation, and exponential backoff retry loops.
- **Judge Registry & Templates**: Pluggable registry and template models isolating prompt definitions and rubrics from execution code.
- **Initial Cognitive Judges**: Built-in judges for `Faithfulness`, `Groundedness`, `AnswerCorrectness`, and `Hallucination`.
- **Dataset Engine**: First-class support for registering, validating, and loading versioned golden datasets in JSON and JSONL formats with semantic versioning (SemVer) checks.
- **Experiment Engine**: Grouping evaluation runs into experiments, comparing performance deltas against chronological baselines, and auto-generating markdown reports.
- **Reproducible Benchmarks**: Decatur runner that uses a structured [BenchmarkConfig](file:///d:/AI/evalforge/src/domain/entities/benchmark_config.py) housing concurrency caps, retry delay backoffs, and evaluator filters.
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

### Running the REST API Backend
Start the FastAPI server using Uvicorn:
```bash
.venv\Scripts\python -m uvicorn src.adapters.api.app:app --host 0.0.0.0 --port 8000 --reload
```
- **API Swagger Documentation**: http://localhost:8000/docs
- **Health check**: http://localhost:8000/health

### Running the Next.js Frontend
Install dependencies and run the frontend client:
```bash
cd frontend
npm install
npm run dev
```
- **Frontend Web UI**: http://localhost:3000

### Deployment with Docker Compose
To build and launch the integrated FastAPI backend and Next.js frontend services:
```bash
docker-compose up --build
```
- **Integrated Backend Endpoint**: http://localhost:8000
- **Integrated Frontend Client**: http://localhost:3000

