from typing import Any

from pydantic import BaseModel, Field

from src.domain.value_objects import Cost, Latency, TokenUsage


class ToolCall(BaseModel):
    """Represents a tool invocation by the agent SUT."""

    tool_name: str = Field(..., description="Name of the tool called")
    arguments: dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool"
    )
    success: bool = Field(default=True, description="Whether the tool execution succeeded")
    error: str | None = Field(default=None, description="Error message if the tool failed")


class Step(BaseModel):
    """Represents a single reasoning-action-observation step in an agent trajectory."""

    step_number: int = Field(..., ge=1, description="1-indexed step order")
    thought: str | None = Field(
        default=None, description="The internal reasoning/thought process of the agent"
    )
    tool_calls: list[ToolCall] = Field(
        default_factory=list, description="Tool calls executed in this step"
    )
    observation: str | dict[str, Any] | None = Field(
        default=None, description="Observation or result returned by the environment/tools"
    )
    response: str | None = Field(
        default=None, description="Final response text returned to the user (if terminal)"
    )
    token_usage: TokenUsage = Field(
        default_factory=TokenUsage.zero, description="Token usage for this step"
    )
    cost: Cost = Field(default_factory=Cost.zero, description="Financial cost for this step")
    latency: Latency = Field(default_factory=Latency.zero, description="Latency for this step")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context or provider-specific logs"
    )


class Trajectory(BaseModel):
    """Represents the complete execution trace of an agent run."""

    steps: list[Step] = Field(default_factory=list, description="Ordered steps of the execution")
    total_token_usage: TokenUsage = Field(
        default_factory=TokenUsage.zero, description="Total tokens across all steps"
    )
    total_cost: Cost = Field(default_factory=Cost.zero, description="Total cost across all steps")
    total_latency: Latency = Field(
        default_factory=Latency.zero, description="Total duration of the agent run"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata such as engine versions, tags, etc."
    )

    def add_step(self, step: Step) -> None:
        """Adds a step to the trajectory and aggregates token usage, cost, and latency."""
        self.steps.append(step)
        self.total_token_usage = self.total_token_usage + step.token_usage
        self.total_cost = self.total_cost + step.cost
        self.total_latency = self.total_latency + step.latency

    @property
    def final_response(self) -> str | None:
        """Returns the final response of the trajectory if present in the last steps."""
        for step in reversed(self.steps):
            if step.response:
                return step.response
        return None

    @property
    def all_tool_calls(self) -> list[ToolCall]:
        """Returns all tool calls made during the entire trajectory."""
        calls = []
        for step in self.steps:
            calls.extend(step.tool_calls)
        return calls
