# AI Agent Evaluation Framework for Travel and Accommodation Platform (Booking.com 2026 Inspired)

This repository contains a production-grade AI Agent Evaluation Framework designed to benchmark, audit, and observe AI agents running on travel and accommodation platforms.

## 🚀 Key Features
- **Evaluation Datasets**: Multi-turn travel itineraries and bookings with complex constraints (budget, location, family size).
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
├── .agents/                    # Workspace Customizations
│   └── AGENTS.md               # Custom agent rules
├── docs/
│   ├── adr/                    # Architecture Decision Records
│   │   ├── 0001-record-architecture-decisions.md
│   │   ├── 0002-tech-stack-and-architecture-patterns.md
│   │   └── 0003-pluggable-llm-provider-and-metrics-specification.md
│   └── architecture.md         # Overall architectural blueprint
├── src/
│   ├── domain/                 # Core Entities, Value Objects & interfaces
│   │   ├── entities/           # Trajectory, Step, Dataset, EvaluationRun
│   │   ├── value_objects/      # TokenUsage, Cost, Latency
│   │   └── interfaces/         # Contracts for LLM, Repositories, Evaluators
│   ├── use_cases/              # Evaluation logic & metric calculators
│   ├── adapters/               # Concrete integrations (Gemini, Sqlite)
│   └── infrastructure/         # Environment setup & Mock System under Test
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
