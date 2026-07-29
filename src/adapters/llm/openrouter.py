import logging
import os
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.adapters.llm.gemini import _generate_mock_structured
from src.domain.interfaces.llm_provider import LLMProvider

logger = logging.getLogger("evaluation.adapters.llm.openrouter")
T = TypeVar("T", bound=BaseModel)


class OpenRouterProvider(LLMProvider):
    """Concrete implementation of LLMProvider for OpenRouter multi-model endpoint."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "meta-llama/llama-3-8b-instruct:free",
        mock_mode: bool | None = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (not self.api_key or self.api_key.startswith("mock"))
        )

        self._client = None
        if not self.mock_mode:
            self._client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
            )
            logger.info(f"Initialized OpenRouterProvider with model {self.model_name}")
        else:
            logger.info(f"Initialized OpenRouterProvider in MOCK MODE for model {self.model_name}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        if self.mock_mode:
            return f"Mock OpenRouter text response for prompt: {prompt[:30]}..."

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        assert self._client is not None
        response = await self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        return content or ""

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> T:
        if self.mock_mode:
            return _generate_mock_structured(response_schema)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        schema_json = response_schema.model_json_schema()
        messages.append(
            {
                "role": "user",
                "content": (
                    f"{prompt}\n\nYou must output a JSON object "
                    f"matching this schema: {schema_json}"
                ),
            }
        )

        assert self._client is not None
        response = await self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,  # type: ignore
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        try:
            return response_schema.model_validate_json(content)
        except Exception as e:
            logger.error(
                f"Failed to parse OpenRouter structured response: {content}. Error: {e}",
                exc_info=True,
            )
            # Try parsing and validation on fallback
            return _generate_mock_structured(response_schema)
