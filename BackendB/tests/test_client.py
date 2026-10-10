"""Unit tests for llm/client.py using mock transport."""
import asyncio
import pytest
from pydantic import BaseModel
from llm.client import (
    GeminiClient,
    LLMClientError,
    clean_json_text,
    scrub_pii,
    is_transient_or_rate_limit,
)


class DummyResponseModel(BaseModel):
    message: str
    count: int


def test_scrub_pii():
    """Verify sensitive tokens, emails, and phone numbers are scrubbed."""
    raw = "Contact test.user@example.com or +1 415 555 2671 with key AIzaSyA1234567890123456789012345678901"
    clean = scrub_pii(raw)
    assert "test.user@example.com" not in clean
    assert "[REDACTED_EMAIL]" in clean
    assert "[REDACTED_PHONE]" in clean
    assert "[REDACTED_API_KEY]" in clean


def test_clean_json_text():
    """Verify markdown code fences are stripped cleanly."""
    fenced = "```json\n{\"foo\": \"bar\"}\n```"
    assert clean_json_text(fenced) == '{"foo": "bar"}'


def test_is_transient_or_rate_limit():
    """Verify detection of transient errors and rate limits."""
    assert is_transient_or_rate_limit(Exception("429 Resource Exhausted")) is True
    assert is_transient_or_rate_limit(Exception("503 Service Unavailable")) is True
    assert is_transient_or_rate_limit(Exception("Model high demand")) is True
    assert is_transient_or_rate_limit(Exception("Fatal syntax error")) is False


@pytest.mark.asyncio
async def test_generate_structured_mock_success():
    """GeminiClient parses valid JSON from transport into target Pydantic model."""
    def mock_transport(prompt, schema):
        return '{"message": "success", "count": 42}'

    client = GeminiClient(transport=mock_transport)
    result = await client.generate_structured("test prompt", DummyResponseModel)
    assert isinstance(result, DummyResponseModel)
    assert result.message == "success"
    assert result.count == 42


@pytest.mark.asyncio
async def test_generate_structured_timeout():
    """Client raises LLMClientError on timeout."""
    async def slow_transport(prompt, schema):
        await asyncio.sleep(0.5)
        return '{"message": "too late", "count": 0}'

    client = GeminiClient(timeout=0.1, transport=slow_transport, max_retries=1)
    with pytest.raises(LLMClientError) as exc_info:
        await client.generate_structured("slow prompt", DummyResponseModel)
    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_generate_structured_retries_on_invalid_json():
    """Client retries up to max_retries when invalid JSON is returned."""
    attempts = {"count": 0}

    def flaky_transport(prompt, schema):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return "not-json"
        return '{"message": "recovered", "count": 1}'

    client = GeminiClient(max_retries=3, transport=flaky_transport)
    result = await client.generate_structured("test", DummyResponseModel)
    assert attempts["count"] == 2
    assert result.message == "recovered"


def test_generate_structured_sync_wrapper():
    """Synchronous wrapper works cleanly in synchronous callers."""
    def mock_transport(prompt, schema):
        return '{"message": "sync ok", "count": 7}'

    client = GeminiClient(transport=mock_transport)
    result = client.generate_structured_sync("prompt", DummyResponseModel)
    assert result.message == "sync ok"
    assert result.count == 7
