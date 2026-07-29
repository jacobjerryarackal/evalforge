# ADR-0003: Pluggable LLM Provider & Evaluation Metrics Specification

## Status
Approved

## Context
Our framework needs to evaluate travel agents across multiple dimensions (retrieval, reasoning, policy, cost, correctness). Calculating these metrics often requires calling an LLM (e.g. LLM-as-a-judge for groundedness) or calculating standard heuristic calculations (e.g. token counts, exact keyword match).
To make our evaluation suite truly independent of any single model provider (preventing OpenAI/Gemini vendor lock-in), we need a unified interface for model interactions, and a structured, extensible interface for metric evaluation.

## Decision
We implement the following:

1. **LLM Provider Interface**:
   - A standard interface `LLMProvider` defined in `src/domain/interfaces/llm_provider.py`.
   - Implementations for different providers (`GeminiProvider`, `OllamaProvider`, `OpenRouterProvider`) will be written in `src/adapters/llm/`.
   - The interface will provide async methods for:
     - `generate_text(prompt: str, system_instruction: str | None = None, response_schema: type[T] | None = None) -> str`
     - `generate_structured(prompt: str, response_schema: type[T]) -> T` (crucial for LLM-as-a-judge metrics that must output JSON matching a Pydantic schema).

2. **Metrics Design Pattern**:
   - A base abstract class `BaseEvaluator` will be defined in `src/domain/interfaces/evaluator.py`.
   - Each metric (e.g., `FaithfulnessEvaluator`, `ContextRecallEvaluator`) will be implemented as a use case in `src/use_cases/evaluators/`.
   - Each evaluator implements:
     - `async def evaluate(self, input_data: EvaluationInput) -> MetricResult`
   - Evaluation metrics are classified into:
     - **Deterministic Metrics**: E.g., `Latency`, `TokenUsage`, `Cost`, `ToolCallSuccessRate` (no LLM required).
     - **Retrieval Metrics**: E.g., `ContextPrecision`, `ContextRecall` (compares retrieved context against ground truth).
     - **LLM-as-a-Judge Metrics**: E.g., `Groundedness`, `AnswerCorrectness`, `SafetyPolicyCompliance` (uses LLM with specialized prompts to score SUT trajectories).

## Consequences
- **Positive**:
  - We can run local, free evaluations using Ollama (`llama3` or `mistral`) for debugging, and switch to Gemini Flash for benchmark sweeps to save costs, without modifying our evaluators.
  - Adding a new metric is as simple as creating a new subclass of `BaseEvaluator`.
  - Structured output capabilities allow us to get reliable, machine-readable validation reports from LLM judges.
- **Negative**:
  - Requires implementing structured JSON parsing for local models that may not natively support structured JSON mode (mitigated by using Pydantic validation on the outputs and retrying).
