from typing import Any

from pydantic import BaseModel, Field


class JudgeResult(BaseModel):
    """Represents the structured response from an LLM Judge."""

    score: float | bool = Field(
        ..., description="Evaluation score, usually 0.0 - 1.0 or True/False"
    )
    reasoning: str = Field(..., description="Explanatory reasoning for the score")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence level in the judgment")
    raw_output: str | None = Field(default=None, description="The raw, unparsed model output")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata e.g., model name, tokens used"
    )
