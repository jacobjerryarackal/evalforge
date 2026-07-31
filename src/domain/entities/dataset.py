from typing import Any

from pydantic import BaseModel, Field, model_validator


class GoldenTestCase(BaseModel):
    """Represents a single reference test scenario for agent evaluation."""

    id: str = Field(..., description="Unique identifier for the test case")
    difficulty: str = Field(default="Medium", description="Difficulty level (e.g. Easy, Medium, Hard, Expert)")
    category: str = Field(default="general", description="Test case category")
    user_query: str = Field(..., description="The user prompt or instruction")
    retrieved_context: str | None = Field(default=None, description="Ground truth context snippet")
    expected_tool_calls: list[Any] = Field(default_factory=list, description="Expected tool call structures")
    expected_answer: str | None = Field(default=None, description="Reference final response")
    latency_constraint: float | None = Field(default=None, description="Max latency limit in seconds")
    token_constraint: int | None = Field(default=None, description="Max token usage limit")
    cost_constraint: float | None = Field(default=None, description="Max cost limit in USD")
    expected_metrics: dict[str, float] = Field(default_factory=dict, description="Target metric thresholds")
    expected_judge_scores: dict[str, float] = Field(default_factory=dict, description="Target judge score thresholds")
    failure_mode: str = Field(default="None", description="Target failure category")
    ground_truth_context: list[str] = Field(default_factory=list, description="Ground truth context list")
    custom_constraints: dict[str, Any] = Field(default_factory=dict, description="Additional custom constraints")

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "case_id" in data and "id" not in data:
                data["id"] = data["case_id"]
            if "input_query" in data and "user_query" not in data:
                data["user_query"] = data["input_query"]
            if "expected_output" in data and "expected_answer" not in data:
                data["expected_answer"] = data["expected_output"]
            
            # Synchronize retrieved_context and ground_truth_context list
            if "ground_truth_context" in data and "retrieved_context" not in data:
                gt = data["ground_truth_context"]
                data["retrieved_context"] = gt[0] if gt else None
            elif "retrieved_context" in data and "ground_truth_context" not in data:
                rc = data["retrieved_context"]
                data["ground_truth_context"] = [rc] if rc else []
            
            # Map constraints
            if "constraints" in data:
                cons = data["constraints"] or {}
                if "max_latency" in cons and "latency_constraint" not in data:
                    data["latency_constraint"] = cons["max_latency"]
                if "max_tokens" in cons and "token_constraint" not in data:
                    data["token_constraint"] = cons["max_tokens"]
                if "max_cost" in cons and "cost_constraint" not in data:
                    data["cost_constraint"] = cons["max_cost"]
                
                data["custom_constraints"] = cons
            
            # Map metadata
            if "metadata" in data:
                meta = data["metadata"] or {}
                for f in ["difficulty", "category", "expected_metrics", "expected_judge_scores", "failure_mode"]:
                    if f in meta and f not in data:
                        data[f] = meta[f]
        return data

    @property
    def case_id(self) -> str:
        return self.id

    @property
    def input_query(self) -> str:
        return self.user_query

    @property
    def expected_output(self) -> str | None:
        return self.expected_answer

    @property
    def constraints(self) -> dict[str, Any]:
        c = dict(self.custom_constraints)
        if self.latency_constraint is not None:
            c["max_latency"] = self.latency_constraint
        if self.token_constraint is not None:
            c["max_tokens"] = self.token_constraint
        if self.cost_constraint is not None:
            c["max_cost"] = self.cost_constraint
        return c


    @property
    def metadata(self) -> dict[str, Any]:
        return {
            "difficulty": self.difficulty,
            "category": self.category,
            "expected_metrics": self.expected_metrics,
            "expected_judge_scores": self.expected_judge_scores,
            "failure_mode": self.failure_mode,
        }



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
