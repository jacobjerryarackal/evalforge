import pytest
from pydantic import BaseModel, Field

from src.adapters.llm.gemini import GeminiProvider
from src.adapters.llm.ollama import OllamaProvider
from src.adapters.llm.openrouter import OpenRouterProvider


class JudgeScore(BaseModel):
    score: float = Field(..., description="The quantitative score")
    reason: str = Field(..., description="Reasoning for the score")
    passed: bool = Field(..., description="Whether it passed validation")


@pytest.mark.anyio
async def test_gemini_provider_mock():
    provider = GeminiProvider(mock_mode=True)
    assert provider.mock_mode is True

    # Test text generation
    text = await provider.generate_text("Verify this prompt")
    assert isinstance(text, str)
    assert "Mock Gemini" in text

    # Test structured generation
    structured = await provider.generate_structured("Verify criteria", JudgeScore)
    assert isinstance(structured, JudgeScore)
    assert isinstance(structured.score, float)
    assert isinstance(structured.reason, str)
    assert isinstance(structured.passed, bool)


@pytest.mark.anyio
async def test_ollama_provider_mock():
    provider = OllamaProvider(mock_mode=True)
    assert provider.mock_mode is True

    # Test text generation
    text = await provider.generate_text("Verify this prompt")
    assert isinstance(text, str)
    assert "Mock Ollama" in text

    # Test structured generation
    structured = await provider.generate_structured("Verify criteria", JudgeScore)
    assert isinstance(structured, JudgeScore)
    assert isinstance(structured.score, float)
    assert isinstance(structured.reason, str)
    assert isinstance(structured.passed, bool)


@pytest.mark.anyio
async def test_openrouter_provider_mock():
    provider = OpenRouterProvider(mock_mode=True)
    assert provider.mock_mode is True

    # Test text generation
    text = await provider.generate_text("Verify this prompt")
    assert isinstance(text, str)
    assert "Mock OpenRouter" in text

    # Test structured generation
    structured = await provider.generate_structured("Verify criteria", JudgeScore)
    assert isinstance(structured, JudgeScore)
    assert isinstance(structured.score, float)
    assert isinstance(structured.reason, str)
    assert isinstance(structured.passed, bool)
