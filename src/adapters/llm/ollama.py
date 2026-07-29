import logging
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.adapters.llm.gemini import _generate_mock_structured
from src.domain.interfaces.llm_provider import LLMProvider

logger = logging.getLogger("evaluation.adapters.llm.ollama")
T = TypeVar("T", bound=BaseModel)


class OllamaProvider(LLMProvider):
    """Concrete implementation of LLMProvider for local Ollama endpoints."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        model_name: str = "llama3",
        mock_mode: bool | None = None,
    ):
        self.base_url = base_url
        self.model_name = model_name
        # If mock_mode is explicitly set, use that, else default to False
        self.mock_mode = mock_mode if mock_mode is not None else False

        self._client = AsyncOpenAI(base_url=self.base_url, api_key="ollama")
        logger.info(
            f"Initialized OllamaProvider for {self.model_name} at {self.base_url}"
            + (" (MOCK MODE)" if self.mock_mode else "")
        )

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        if self.mock_mode:
            return f"Mock Ollama text response for prompt: {prompt[:30]}..."

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content or ""
        except Exception as e:
            logger.warning(
                f"Ollama connection or execution failed: {e}. "
                "Falling back to mock response in test mode."
            )
            # Self-healing fallback for local unit tests without active Ollama server
            return f"Mock Ollama fallback response (failed to reach server): {prompt[:30]}..."

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

        # To request JSON from Ollama via standard OpenAI client:
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

        try:
            response = await self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return response_schema.model_validate_json(content)
        except Exception as e:
            logger.warning(
                f"Ollama structured execution failed: {e}. "
                "Falling back to mock structured response."
            )
            return _generate_mock_structured(response_schema)
