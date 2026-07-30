from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.dataset import GoldenDataset


class RetryPolicy(BaseModel):
    """Configuration options for retrying failed SUT operations."""

    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    initial_delay: float = Field(
        default=1.0, description="Initial delay before first retry, in seconds"
    )
    backoff_factor: float = Field(
        default=2.0, description="Multiplier applied to delay after each retry"
    )


class BenchmarkConfig(BaseModel):
    """First-class configuration for executing an evaluation benchmark."""

    dataset: GoldenDataset = Field(..., description="The golden dataset to evaluate against")
    provider: str = Field(
        ..., description="LLM provider name (e.g., 'gemini', 'ollama', 'openrouter')"
    )
    evaluators: list[str] = Field(
        default_factory=list,
        description=(
            "Names of metrics/evaluators to execute. "
            "If empty, all registered evaluators are run."
        ),
    )
    concurrency: int = Field(default=3, description="Maximum concurrent test cases to execute")
    retry_policy: RetryPolicy = Field(
        default_factory=RetryPolicy,
        description="Retry behavior configuration for LLM/SUT failures",
    )
    execution_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary model or runner specific parameters (e.g., temperature, max_tokens)",
    )
