"""InterviewIQ - Gemini Client Module

Provides a robust, production-ready async & sync wrapper around the official
Google GenAI SDK (google-genai) with structured Pydantic output, exponential
backoff retry, request timeout, PII-scrubbed logging, and mock support.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import logging
import re
import time
from typing import Any, Callable, Dict, Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError

import config
from llm.quota_guard import quota_guard, QuotaBlocked

logger = logging.getLogger("interviewiq.llm")

T = TypeVar("T", bound=BaseModel)


class LLMClientError(Exception):
    """Structured error raised by GeminiClient for callers to handle gracefully."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def __str__(self) -> str:
        code_str = f" [status={self.status_code}]" if self.status_code else ""
        return f"LLMClientError{code_str}: {self.message}"


# Regex patterns for redacting sensitive PII from debug logs
_KEY_RE = re.compile(r"(AIza[0-9A-Za-z-_]{30,}|AQ\.[0-9A-Za-z-_]{30,})")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"(?<![A-Za-z0-9])\+?\d[\d\s().-]{7,}\d(?![A-Za-z0-9])")


def scrub_pii(text: str) -> str:
    """Sanitize logs to ensure personal identifiers and API keys are never written."""
    if not isinstance(text, str):
        return str(text)
    sanitized = _KEY_RE.sub("[REDACTED_API_KEY]", text)
    sanitized = _EMAIL_RE.sub("[REDACTED_EMAIL]", sanitized)
    return _PHONE_RE.sub("[REDACTED_PHONE]", sanitized)


def clean_json_text(text: str) -> str:
    """Strip markdown formatting fences that models occasionally include."""
    clean = text.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)
    return clean.strip()


def is_transient_or_rate_limit(error: Exception) -> bool:
    """Detect if an exception is rate-limiting or temporary service unavailability."""
    msg = str(error).lower()
    return any(marker in msg for marker in (
        "429", "503", "resource_exhausted", "quota", "rate", "limit",
        "unavailable", "high demand", "overloaded", "temporary"
    ))


class GeminiClient:
    """Official Google GenAI client wrapper for InterviewIQ Backend B."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        transport: Optional[Callable[[str, Any], Any]] = None,
    ):
        self.api_key = api_key if api_key is not None else config.GEMINI_API_KEY
        self.model = model or config.GEMINI_MODEL
        self.temperature = config.GEMINI_TEMPERATURE if temperature is None else temperature
        self.timeout = config.GEMINI_TIMEOUT if timeout is None else timeout
        self.max_retries = config.GEMINI_MAX_RETRIES if max_retries is None else max_retries
        self._custom_transport = transport
        self._genai_client = None

    def _get_sdk_client(self):
        if self._genai_client is None:
            if not self.api_key:
                raise LLMClientError("GEMINI_API_KEY is not configured. Please set it in .env or pass it explicitly.")
            from google import genai
            self._genai_client = genai.Client(api_key=self.api_key)
        return self._genai_client

    async def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        purpose: str = "generation",
    ) -> T:
        """Asynchronously call Gemini and validate the response against a Pydantic model.

        Retries on transient network errors, rate limits, or invalid JSON.
        """
        try:
            quota_guard.check()
        except QuotaBlocked as qb:
            raise LLMClientError(str(qb))

        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            start_time = time.monotonic()
            raw_text = ""

            try:
                # 1. Custom mock transport (used in unit tests)
                if self._custom_transport is not None:
                    if inspect.iscoroutinefunction(self._custom_transport):
                        raw_result = await asyncio.wait_for(
                            self._custom_transport(prompt, response_model),
                            timeout=self.timeout
                        )
                    else:
                        loop = asyncio.get_running_loop()
                        raw_result = await asyncio.wait_for(
                            loop.run_in_executor(None, self._custom_transport, prompt, response_model),
                            timeout=self.timeout
                        )

                    latency = time.monotonic() - start_time
                    if isinstance(raw_result, response_model):
                        logger.info("Transport returned instance for %s in %.2fs", purpose, latency)
                        return raw_result
                    raw_text = raw_result if isinstance(raw_result, str) else json.dumps(raw_result)

                # 2. Live Google GenAI SDK call
                else:
                    client = self._get_sdk_client()
                    from google.genai import types

                    config_kwargs: Dict[str, Any] = {
                        "temperature": self.temperature,
                        "response_mime_type": "application/json",
                    }
                    try:
                        gen_config = types.GenerateContentConfig(
                            response_schema=response_model,
                            **config_kwargs
                        )
                    except Exception:
                        # Fallback for environments with schema type differences
                        gen_config = types.GenerateContentConfig(**config_kwargs)

                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=self.model,
                            contents=prompt,
                            config=gen_config,
                        ),
                        timeout=self.timeout
                    )
                    latency = time.monotonic() - start_time
                    raw_text = response.text or ""

                # 3. Clean and parse JSON into Pydantic model
                cleaned_json = clean_json_text(raw_text)
                parsed_instance = response_model.model_validate_json(cleaned_json)

                latency = time.monotonic() - start_time
                logger.info(
                    "Gemini %s succeeded on attempt %d (latency: %.2fs, model: %s)",
                    purpose, attempt, latency, self.model
                )
                return parsed_instance

            except asyncio.TimeoutError:
                last_error = LLMClientError(f"Gemini API request timed out after {self.timeout}s")
                logger.warning("Attempt %d for %s timed out after %.1fs", attempt, purpose, self.timeout)

            except ValidationError as ve:
                last_error = LLMClientError(f"Pydantic schema validation failed: {ve}", details={"raw": scrub_pii(raw_text)[:300]})
                logger.warning("Attempt %d for %s failed schema validation: %s", attempt, purpose, scrub_pii(str(ve)))

            except json.JSONDecodeError as je:
                last_error = LLMClientError(f"Invalid JSON returned: {je}", details={"raw": scrub_pii(raw_text)[:300]})
                logger.warning("Attempt %d for %s returned malformed JSON: %s", attempt, purpose, je)

            except Exception as ex:
                if isinstance(ex, LLMClientError) and "GEMINI_API_KEY" in ex.message:
                    raise  # Configuration error, retry is futile

                last_error = ex
                logger.warning("Attempt %d for %s failed: %s", attempt, purpose, scrub_pii(str(ex)))
                if quota_guard.should_stop(str(ex)):
                    quota_guard.trip(str(ex))
                    raise LLMClientError(f"{purpose} stopped: daily Gemini quota exhausted")

            # Exponential backoff before next attempt
            if attempt < self.max_retries:
                if is_transient_or_rate_limit(last_error):
                    backoff = config.RATE_LIMIT_BACKOFF_BASE * (2 ** (attempt - 1))
                else:
                    backoff = 1.5 * attempt
                logger.info("Backing off for %.1fs before attempt %d...", backoff, attempt + 1)
                await asyncio.sleep(backoff)

        # All retries exhausted
        error_msg = f"{purpose} failed after {self.max_retries} attempts: {last_error}"
        logger.error(scrub_pii(error_msg))
        raise LLMClientError(error_msg)

    def generate_structured_sync(
        self,
        prompt: str,
        response_model: Type[T],
        purpose: str = "generation",
    ) -> T:
        """Synchronous wrapper around generate_structured for non-async environments."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # In an already running event loop, create task or run in executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    lambda: asyncio.run(self.generate_structured(prompt, response_model, purpose))
                )
                return future.result()
        else:
            return loop.run_until_complete(
                self.generate_structured(prompt, response_model, purpose)
            )
