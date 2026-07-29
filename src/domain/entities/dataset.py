from typing import Any

from pydantic import BaseModel, Field


class GoldenTestCase(BaseModel):
    """Represents a single reference test scenario for agent evaluation."""

    case_id: str = Field(..., description="Unique identifier for the test case")
    input_query: str = Field(
        ..., description="The user prompt or instruction to feed to the agent SUT"
    )
    expected_output: str | None = Field(
        default=None, description="The reference/ground truth final response"
    )
    ground_truth_context: list[str] = Field(
        default_factory=list,
        description="Reference source contexts that must be retrieved or used to answer",
    )
    expected_tool_calls: list[str] = Field(
        default_factory=list,
        description="Names of tools expected to be invoked during this test run",
    )
    constraints: dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value pairs of constraints (e.g., max_price: 300, location: 'Paris')",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary tags, e.g., category: 'flight', difficulty: 'hard'",
    )


class GoldenDataset(BaseModel):
    """Represents a versioned collection of golden test cases used for evaluation."""

    dataset_id: str = Field(..., description="Unique identifier for the dataset")
    name: str = Field(..., description="Human-readable name of the dataset")
    description: str | None = Field(
        default=None, description="Purpose or description of the dataset"
    )
    version: str = Field(default="1.0.0", description="Semantic version of this dataset")
    test_cases: list[GoldenTestCase] = Field(default_factory=list, description="List of test cases")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Dataset metadata")

    def get_case(self, case_id: str) -> GoldenTestCase | None:
        """Helper to retrieve a specific test case by its ID."""
        for case in self.test_cases:
            if case.case_id == case_id:
                return case
        return None
