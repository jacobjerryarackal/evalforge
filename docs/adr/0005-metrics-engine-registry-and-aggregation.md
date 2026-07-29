# ADR-0005: Metrics Engine Registry and Aggregation Design

## Status
Approved

## Context
For Sprint 2B, we must design and implement the reusable Metrics Engine that executes and aggregates scoring metrics. To keep the framework extensible and maintain architectural boundaries:
1. `BenchmarkRunner` must run metrics dynamically without direct imports of concrete metrics, satisfying Dependency Inversion.
2. Run aggregation statistics (averages, totals) must be separated from case execution to allow calculations to evolve independently.

## Decision
We make the following design decisions:

1. **Registry Pattern for Evaluator Discovery**:
   - We implement a centralized [MetricRegistry](file:///d:/AI/evalforge/src/use_cases/metrics/registry.py). Concrete metrics inherit from `BaseEvaluator` and register themselves into this registry.
   - `BenchmarkRunner` receives `MetricRegistry` via constructor injection and queries the registry dynamically using string-based metric names. This decouples the runner from concrete evaluator classes completely.

2. **Dedicated Aggregation Engine**:
   - We implement [AggregationEngine](file:///d:/AI/evalforge/src/use_cases/metrics/aggregation.py) in the Use Cases layer. This class accepts a list of case evaluation results and computes totals (cost, tokens), averages (latency, metric scores), and structures the summary dictionary.
   - Isolating this logic from the `EvaluationRun` domain entity aligns with the Single Responsibility Principle and simplifies future extensions (like computing P99 latencies or weighted averages).

3. **Deterministic Evaluator Base**:
   - We implement 6 base deterministic evaluators (`Latency`, `TokenUsage`, `Cost`, `ToolCalling`, `ContextPrecision`, and `ContextRecall`).
   - Threshold limits (like `max_latency`, `max_cost`) can be dynamically customized per-case via `GoldenTestCase.constraints`, falling back to default evaluator configurations if not present.

## Consequences
- **Positive**:
  - High extensibility: adding new heuristics or LLM-as-a-judge metrics requires zero changes to the execution loop or `BenchmarkRunner`.
  - Strong encapsulation: the aggregation engine is fully mockable and testable in isolation.
  - Granular configurations: per-test-case threshold constraints are supported natively.
- **Negative**:
  - Requires developers to register custom metrics before running benchmarks.
  - *Mitigation*: We expose `create_default_registry()` which registers all standard metrics automatically out of the box.
