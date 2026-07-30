import asyncio
import json
import logging
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.judge import JudgeResult
from src.domain.interfaces.llm_provider import LLMProvider
from src.use_cases.judges.templates import JudgePromptTemplate

logger = logging.getLogger("evaluation.judges.engine")


class LLMJudgeOutputSchema(BaseModel):
    """Pydantic schema representing the structured output expected from the LLM."""

    score: float = Field(..., description="The quantitative evaluation score")
    reasoning: str = Field(..., description="Explanation/justification for the score")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")


class LLMJudgeEngine:
    """Reusable execution engine for LLM-based judges."""

    def __init__(
        self,
        provider: LLMProvider,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> None:
        self.provider = provider
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor

    async def execute(
        self,
        template: JudgePromptTemplate,
        variables: dict[str, Any],
        output_schema: type[LLMJudgeOutputSchema] = LLMJudgeOutputSchema,
    ) -> JudgeResult:
        """Executes a judge prompt template and parses the result, handling retries."""
        system_instruction = template.render_system(**variables)
        prompt = template.render_user(**variables)

        delay = self.initial_delay
        last_error: Exception | None = None
        raw_output: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # 1. Try structured generation first
                try:
                    structured_res = await self.provider.generate_structured(
                        prompt=prompt,
                        response_schema=output_schema,
                        system_instruction=system_instruction,
                        temperature=0.0,
                    )
                    conf = max(0.0, min(1.0, float(structured_res.confidence)))
                    return JudgeResult(
                        score=structured_res.score,
                        reasoning=structured_res.reasoning,
                        confidence=conf,
                        raw_output=str(structured_res.model_dump()),
                        metadata={"attempt": attempt + 1, "generation_mode": "structured"},
                    )
                except Exception as e:
                    logger.warning(
                        f"Structured generation failed on attempt {attempt + 1}: {e}. "
                        "Falling back to text generation and manual parsing."
                    )
                    # 2. Fallback to text generation and manual JSON parsing
                    raw_output = await self.provider.generate_text(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        temperature=0.0,
                    )
                    parsed_data = self._parse_json_from_text(raw_output)
                    structured_res = output_schema.model_validate(parsed_data)
                    conf = max(0.0, min(1.0, float(structured_res.confidence)))
                    return JudgeResult(
                        score=structured_res.score,
                        reasoning=structured_res.reasoning,
                        confidence=conf,
                        raw_output=raw_output,
                        metadata={"attempt": attempt + 1, "generation_mode": "fallback_parsed"},
                    )
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM Judge execution attempt {attempt + 1}/{self.max_retries + 1} "
                    f"failed: {e}"
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= self.backoff_factor

        # If we exhausted all retries, return failure JudgeResult
        error_msg = (
            f"LLM Judge execution failed after {self.max_retries + 1} attempts. "
            f"Last error: {last_error}"
        )
        logger.error(error_msg)
        return JudgeResult(
            score=0.0,
            reasoning=error_msg,
            confidence=0.0,
            raw_output=raw_output,
            metadata={"error": str(last_error), "attempts_made": self.max_retries + 1},
        )

    def _parse_json_from_text(self, text: str) -> dict[str, Any]:
        """Utility to extract and parse JSON from a raw model output string."""
        text = text.strip()
        # Find start and end of JSON block if wrapped in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            json_str = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            json_str = text[start:end].strip()
        else:
            # Try to find the first '{' and last '}'
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                json_str = text[start : end + 1]
            else:
                json_str = text

        return json.loads(json_str)
