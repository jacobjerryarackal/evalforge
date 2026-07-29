# ADR-0004: SQLite Repository and Travel Agent SUT Design

## Status
Approved

## Context
For Sprint 1, we must implement:
1. A concrete `EvaluationRepository` using SQLite to store golden datasets and evaluation run results on disk.
2. A deterministic `TravelAgentSUT` that exposes realistic travel service APIs through simulated multi-turn tool execution traces.

Since we are executing evaluations concurrently under asyncio, we must ensure that SQLite operations do not block the main event loop. Additionally, the System Under Test (SUT) must produce highly realistic trajectories (with step-by-step thoughts, token costs, latencies, and tool observations) to support future heuristic and cognitive metrics, while remaining 100% deterministic and offline-ready.

## Decision
We make the following design decisions:

1. **SQLite Async Execution**:
   - We implement [SqliteEvaluationRepository](file:///d:/AI/evalforge/src/adapters/repositories/sqlite_repository.py) using the standard library `sqlite3` module.
   - To prevent blocking the asyncio event loop during database disk I/O, all database transactions are offloaded to background threads using `asyncio.to_thread`.
   - We index critical columns (`run_id`, `dataset_id`, `version`) to ensure fast queries.

2. **JSON Document Storage for Trajectories**:
   - Instead of complex relational joins across highly normalized tables for nested classes like `Step` and `ToolCall`, we serialize the full list of `TestCaseEvaluation` and `GoldenTestCase` objects directly to JSON strings stored in TEXT columns (`cases` and `test_cases` respectively).
   - This prevents database schema locking when new metrics or trajectory metadata fields are added.

3. **Deterministic SUT & Catalog Simulation**:
   - We implement a deterministic simulation layer in [services.py](file:///d:/AI/evalforge/src/infrastructure/travel_simulation/services.py) with mock data for Flights, Hotels, Weather, Currency, Attractions, Booking Policy, and User Profile services.
   - The SUT parses the user query and runs an actual programmatic loop that queries these simulation services, wraps the list-based observations in dictionaries (complying with the `Step.observation` schema), and records realistic step-by-step reasoning thoughts, costs, and latencies.

## Consequences
- **Positive**:
  - Thread-safe, non-blocking asynchronous persistence using only the standard library.
  - Zero-configuration local database that works out of the box.
  - SUT trajectories are realistic and fully testable offline, making future evaluations deterministic and fast.
- **Negative**:
  - Storing evaluations as JSON strings makes it harder to run complex SQL aggregations inside SQLite directly.
  - *Mitigation*: The `EvaluationRun` model computes summaries inside Python before saving, and we expose indexable columns on the parent tables.
