# ADR-0006: Platform & REST API Specification

## Status
Accepted

## Context
We need to productize the EvalForge framework, transforming it from a Python library into an evaluation platform. This requires exposing API endpoints, providing a web dashboard for visualization, generating markdown execution reports, and outputting structured telemetry.

## Decisions
1. **API Framework**: We adopt **FastAPI** with **Uvicorn** as the REST hosting engine because of its fast asynchronous capabilities, automatic OpenAPI/Swagger generation, and built-in support for BackgroundTasks.
2. **Asynchronous Execution**: Benchmark runner triggers will run asynchronously via FastAPI `BackgroundTasks`, yielding a `run_id` immediately so client dashboard threads do not block.
3. **Web Dashboard**: We implement a TypeScript **Next.js** single page app layout in a `frontend/` directory, exposing cards, inputs, delta comparison grids, and trace inspectors.
4. **Structured Logging**: We use a custom `JSONFormatter` in python logging to format console/stdout logs as structured JSON lines, providing traceability parameters for metrics.
5. **Deployment**: We configure a multi-container Docker compose environment with a Python FastAPI backend container and a Node Next.js frontend container.

## Consequences
- Clean Architecture adapter boundaries are strictly maintained (REST endpoints contain zero business logic).
- Non-Python clients can trigger and query benchmark runs.
- Production logs can be indexed directly by standard search engines without string regex parsers.
