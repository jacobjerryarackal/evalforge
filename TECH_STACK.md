# TECH_STACK — EvalForge Technology Choices

This document lists the technologies chosen for **EvalForge** and details the engineering rationale behind each selection.

---

## 1. Backend

### Python 3.11+
- **Rationale**: Python is the industry standard for AI, machine learning, and LLM orchestration. Python 3.11 introduces significant performance optimizations (especially in startup time and frame execution) and rich typing features (e.g., `Self`, `Literal`, and enhanced `TypeVar` generics).
- **Alternative Considered**: Node.js/TypeScript. While TS is excellent for web platforms, Python's ecosystem of data analysis (Pandas/Polars) and LLM SDKs (Google Generative AI, OpenAI) provides a much lower friction footprint for AI engineering.

---

## 2. Frontend / Presentation

### Rich (Terminal CLI)
- **Rationale**: `rich` allows creating beautiful, styled terminal dashboards, progress bars, tables, and trace logs. Since EvalForge is designed primarily as a developer tool, a high-fidelity CLI dashboard provides immediate visual feedback during benchmark runs without the overhead of launching separate web servers.

### Jinja2 (Static HTML Reports)
- **Rationale**: Used to compile interactive, styling-rich, single-file HTML reports. Jinja2 templates are fast, require zero frontend build pipelines, and can be immediately opened in any browser or shared over Slack/email.
- **Alternative Considered**: Next.js. Next.js is powerful but adds significant project setup time, package node dependencies, and requires running a node dev server. We will stick to Rich CLI and static HTML for the initial version to keep the developer footprint lightweight.

---

## 3. Database & Storage

### SQLite
- **Rationale**: SQLite is a self-contained, serverless, zero-configuration SQL database engine. It stores data in a single file on disk, making it highly portable. By implementing a clean repository interface, we can read/write structured tables (`evaluation_runs`, `trajectories`, `steps`) with SQL queries while keeping setup times to zero.
- **Alternative Considered**: PostgreSQL. PostgreSQL is excellent for multi-user production platforms but requires installing databases locally, configuring credentials, and managing services. SQLite is ideal for single-developer local evaluation. If needed, the adapter can be upgraded to PostgreSQL later with zero changes to use cases.

---

## 4. Testing

### Pytest & Pytest-Asyncio
- **Rationale**: `pytest` provides a clean, pythonic way to write tests using assertions rather than boilerplate classes. `pytest-asyncio` integrates natively with Python's `asyncio` event loops, which is required to test our concurrent `BenchmarkRunner` use case.

---

## 5. Evaluation & LLM Orchestration

### Pydantic v2
- **Rationale**: Pydantic is used for data parsing, validation, and structured settings configuration. Pydantic v2 is written in Rust and is extremely fast. It allows us to enforce strict schemas for LLM judge outputs, mapping unstructured responses safely back to domain models.

### Google Generative AI SDK (`google-generativeai`)
- **Rationale**: Native SDK to interact with Google Gemini models (e.g. Gemini 1.5 Flash and Gemini 1.5 Pro) with first-class support for features like system instructions, JSON schema enforcement, and tool call responses.

### OpenAI SDK (`openai`)
- **Rationale**: The OpenAI SDK is the de facto standard client library for LLMs. We use it to connect to OpenRouter and other open-source local endpoints (like Ollama) that support OpenAI-compatible API schemas.

---

## 6. Deployment & Environment

### Python Virtual Environment (`.venv`) & `requirements.txt`
- **Rationale**: Standard virtual environment isolation tool. It keeps the workspace clean and isolated. Packages are tracked in `requirements.txt` (and poetry `pyproject.toml` for standard packaging). This avoids docker overhead during initial local development.

---

## 7. Developer Tooling

### Ruff
- **Rationale**: Ruff is an extremely fast Python linter written in Rust. It replaces Flake8, Autopep8, isort, and other tools, running 10-100x faster than traditional linters, yielding immediate developer feedback.

### Black
- **Rationale**: The uncompromising Python code formatter. It standardizes styling across the codebase, eliminating code format debates.

### Mypy
- **Rationale**: Strict static type checker for Python. Enforcing static typing in use cases and adapters prevents runtime bugs, simplifies IDE autocompletion, and aligns with the GStack engineering gate.
