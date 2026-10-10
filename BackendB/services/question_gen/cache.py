"""InterviewIQ - Caching Module

Provides cache abstractions, deterministic hash key generation, in-memory & file
caching with TTL support, and fallback demo plan loader.
"""
from __future__ import annotations

import abc
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import config


_EXCLUDED_PII_KEYS = {
    "name",
    "candidate_name",
    "candidate_id",
    "email",
    "phone",
    "resume",
    "resume_text",
}


def _strip_pii_and_normalize(obj: Any) -> Any:
    """Recursively strip candidate name, resume text, and other PII from cache keys."""
    if isinstance(obj, dict):
        return {
            k: _strip_pii_and_normalize(v)
            for k, v in sorted(obj.items())
            if k.lower() not in _EXCLUDED_PII_KEYS
        }
    if isinstance(obj, list):
        return [_strip_pii_and_normalize(x) for x in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def generate_cache_key(**kwargs: Any) -> str:
    """Computes a deterministic SHA-256 hash key from normalized input parameters.

    Includes settings.difficulty_override, settings.strategy, candidate strengths,
    candidate gaps, and the prompt/rules version.
    Never includes candidate name, resume text, or PII.
    """
    from llm.prompts import PROMPT_VERSION

    normalized: Dict[str, Any] = {}
    normalized["prompt_version"] = kwargs.get("prompt_version", PROMPT_VERSION)

    for k in sorted(kwargs.keys()):
        if k.lower() in _EXCLUDED_PII_KEYS:
            continue
        val = kwargs[k]
        normalized[k] = _strip_pii_and_normalize(val)

    blob = json.dumps(normalized, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class BaseCache(abc.ABC):
    """Abstract Cache Interface that Backend C can subclass for MongoDB caching."""

    @abc.abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached object if present and not expired."""
        pass

    @abc.abstractmethod
    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """Store object in cache with optional TTL."""
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Remove an item from cache."""
        pass

    @abc.abstractmethod
    def clear(self) -> None:
        """Clear all entries from cache."""
        pass


class InMemoryCache(BaseCache):
    """Fast, in-memory cache supporting TTL expiration."""

    def __init__(self, default_ttl: int = config.CACHE_TTL_SECONDS):
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[Dict[str, Any], float]] = {}  # key -> (data, expire_at)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key not in self._store:
            return None
        data, expire_at = self._store[key]
        if expire_at > 0 and time.time() > expire_at:
            del self._store[key]
            return None
        return json.loads(json.dumps(data))  # return copy

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = (time.time() + ttl) if ttl > 0 else 0.0
        self._store[key] = (json.loads(json.dumps(value)), expire_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()


class FileCache(BaseCache):
    """Persistent filesystem cache storing JSON files in a cache directory."""

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None, default_ttl: int = config.CACHE_TTL_SECONDS):
        self.cache_dir = Path(cache_dir or config.CACHE_DIR)
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                record = json.load(f)
            expire_at = record.get("_expire_at", 0.0)
            if expire_at > 0 and time.time() > expire_at:
                p.unlink(missing_ok=True)
                return None
            return record.get("data")
        except Exception:
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = (time.time() + ttl) if ttl > 0 else 0.0
        record = {"_expire_at": expire_at, "data": value}
        p = self._path(key)
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)

    def clear(self) -> None:
        for p in self.cache_dir.glob("*.json"):
            p.unlink(missing_ok=True)


def load_demo_plan(path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Loads the pre-generated verified demo plan for fallback during AI service outages."""
    plan_path = Path(path or config.DEMO_PLAN_PATH)
    if not plan_path.exists():
        raise FileNotFoundError(f"Demo plan not found at {plan_path}")
    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["source"] = "demo_cache"
    return data
