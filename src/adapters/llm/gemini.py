import json
import logging
import os
from types import UnionType
from typing import Any, TypeVar, Union

from pydantic import BaseModel

from src.domain.interfaces.llm_provider import LLMProvider

logger = logging.getLogger("evaluation.adapters.llm.gemini")
T = TypeVar("T", bound=BaseModel)


def _generate_mock_structured(schema: type[T]) -> T:
    """Recursively constructs a mock instance of a Pydantic model with default values."""
    data: dict[str, Any] = {}
    for name, field in schema.model_fields.items():
        field_type = field.annotation
        # Handle Union types like float | bool or Optional types
        origin = getattr(field_type, "__origin__", None)
        if origin is UnionType or origin is Union:  # type: ignore # Handle Union / Optional
            args = getattr(field_type, "__args__", [])
            # Pick the first non-None type
            field_type = next((arg for arg in args if arg is not type(None)), str)

        origin = getattr(field_type, "__origin__", None)
        if field_type is str:
            data[name] = f"Mock {name}"
        elif field_type is int:
            data[name] = 1
        elif field_type is float:
            data[name] = 0.8
        elif field_type is bool:
            data[name] = True
        elif origin is list:
            data[name] = []
        elif origin is dict:
            data[name] = {}
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            data[name] = _generate_mock_structured(field_type)
        else:
            data[name] = None
    return schema.model_validate(data)


class GeminiProvider(LLMProvider):
    """Concrete implementation of LLMProvider for Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-1.5-flash",
        mock_mode: bool | None = None,
    ):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (not self.api_key or self.api_key.startswith("mock"))
        )

        self._client = None
        if not self.mock_mode:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized GeminiProvider with model {self.model_name}")
            except ImportError:
                logger.warning(
                    "google-generativeai package not installed. Falling back to mock mode."
                )
                self.mock_mode = True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini SDK: {e}. Falling back to mock mode.")
                self.mock_mode = True

        if self.mock_mode:
            logger.info(f"Initialized GeminiProvider in MOCK MODE for model {self.model_name}")

    async def generate_text(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> str:
        if self.mock_mode:
            return f"Mock Gemini text response for prompt: {prompt[:30]}..."

        import google.generativeai as genai

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Gemini supports system_instruction on model instantiation, or we can configure it
        # To avoid re-instantiating, we can temporarily set it or use a configured model.
        client = self._client
        if system_instruction:
            client = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )

        # Run model call in thread pool since SDK is synchronous/blocking
        import asyncio

        def _call():
            assert client is not None
            return client.generate_content(prompt, generation_config=generation_config)

        response = await asyncio.to_thread(_call)
        return response.text

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

        import google.generativeai as genai

        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=response_schema,
        )

        client = self._client
        if system_instruction:
            client = genai.GenerativeModel(
                model_name=self.model_name, system_instruction=system_instruction
            )

        import asyncio

        def _call():
            assert client is not None
            return client.generate_content(prompt, generation_config=generation_config)

        response = await asyncio.to_thread(_call)
        text_content = response.text

        try:
            parsed_json = json.loads(text_content)
            return response_schema.model_validate(parsed_json)
        except Exception as e:
            logger.error(
                f"Failed to parse Gemini structured JSON: {text_content}. Error: {e}",
                exc_info=True,
            )
            raise ValueError(f"Failed to validate response against schema: {e}") from e
