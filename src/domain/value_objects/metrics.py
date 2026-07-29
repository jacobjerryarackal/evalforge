from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Value object representing token consumption of a language model call."""

    prompt_tokens: int = Field(default=0, ge=0, description="Number of tokens in the input prompt")
    completion_tokens: int = Field(
        default=0, ge=0, description="Number of tokens in the generated response"
    )
    total_tokens: int = Field(default=0, ge=0, description="Total tokens consumed")

    model_config = {"frozen": True}  # Ensures value object is immutable

    @classmethod
    def zero(cls) -> "TokenUsage":
        return cls(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class Cost(BaseModel):
    """Value object representing the financial cost of operations in USD."""

    amount: float = Field(default=0.0, ge=0.0, description="Cost in USD")
    currency: str = Field(default="USD", description="Currency code")

    model_config = {"frozen": True}

    @classmethod
    def zero(cls) -> "Cost":
        return cls(amount=0.0, currency="USD")

    def __add__(self, other: "Cost") -> "Cost":
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add costs with different currencies: {self.currency} and {other.currency}"
            )
        return Cost(amount=self.amount + other.amount, currency=self.currency)


class Latency(BaseModel):
    """Value object representing time taken in seconds."""

    seconds: float = Field(default=0.0, ge=0.0, description="Duration in seconds")

    model_config = {"frozen": True}

    @classmethod
    def zero(cls) -> "Latency":
        return cls(seconds=0.0)

    def __add__(self, other: "Latency") -> "Latency":
        return Latency(seconds=self.seconds + other.seconds)
