"""Circuit breaker for Gemini quota errors.

Problem it solves: a *daily* quota error ("PerDay", retry in hours) cannot be fixed by retrying
in seconds. Retrying 3 times per call, per group, per round made one demo run take ~3 minutes
and burn even more quota. Once the guard trips, every later call fails instantly until the
quota window has passed.
"""
from __future__ import annotations

import re
import time
from typing import Callable, Optional

_RETRY_IN = re.compile(r"retry in\s*(?:(\d+)h)?\s*(?:(\d+)m)?\s*(\d+(?:\.\d+)?)s", re.I)
_RETRY_DELAY = re.compile(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s", re.I)

LONG_WAIT_SECONDS = 60          # a quota wait longer than this is not worth retrying
DEFAULT_BLOCK_SECONDS = 3600    # used when the error does not say how long to wait


class QuotaBlocked(Exception):
    """Raised by QuotaGuard.check() while the quota window is still closed."""


def parse_retry_delay(msg: str) -> float:
    """Seconds Google asks us to wait, or 0.0 if the message does not say."""
    m = _RETRY_DELAY.search(msg)
    if m:
        return float(m.group(1))
    m = _RETRY_IN.search(msg)
    if m:
        h, mi, s = m.groups()
        return int(h or 0) * 3600 + int(mi or 0) * 60 + float(s)
    return 0.0


def is_quota_error(msg: str) -> bool:
    low = msg.lower()
    return "429" in msg or "resource_exhausted" in low or "quota" in low


def is_hard_quota_error(msg: str) -> bool:
    """True when retrying soon is pointless: a per-day limit, or a long wait."""
    return is_quota_error(msg) and ("perday" in msg.lower() or parse_retry_delay(msg) > LONG_WAIT_SECONDS)


class QuotaGuard:
    def __init__(self, clock: Callable[[], float] = time.time):
        self._clock = clock
        self._blocked_until = 0.0

    def remaining(self) -> float:
        return max(0.0, self._blocked_until - self._clock())

    def check(self) -> None:
        """Call before every LLM call. Raises QuotaBlocked while the guard is tripped."""
        left = self.remaining()
        if left > 0:
            raise QuotaBlocked(f"Gemini quota exhausted; skipping call (about {int(left)}s left)")

    def should_stop(self, msg: str) -> bool:
        return is_hard_quota_error(msg)

    def trip(self, msg: str) -> None:
        delay = parse_retry_delay(msg) or DEFAULT_BLOCK_SECONDS
        self._blocked_until = self._clock() + delay

    def reset(self) -> None:
        self._blocked_until = 0.0


quota_guard = QuotaGuard()   # one shared guard for the whole process
