from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.evaluation import EvaluationRun


class Experiment(BaseModel):
    """Represents an evaluation experiment comparing multiple SUT runs or hypotheses."""

    experiment_id: str = Field(..., description="Unique identifier for the experiment")
    name: str = Field(..., description="Human-readable name of the experiment")
    description: str | None = Field(default=None, description="Hypothesis, goals, or description")
    runs: list[EvaluationRun] = Field(
        default_factory=list,
        description="The history of evaluation runs conducted under this experiment",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary experiment metadata (e.g., prompt templates used, SUT models)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the experiment was created",
    )

    def add_run(self, run: EvaluationRun) -> None:
        """Appends a new evaluation run to this experiment's run history."""
        self.runs.append(run)
