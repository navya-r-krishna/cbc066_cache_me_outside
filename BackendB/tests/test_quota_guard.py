import pytest
from llm.quota_guard import (QuotaGuard, QuotaBlocked, parse_retry_delay,
                             is_hard_quota_error, is_quota_error)

DAILY = ("429 RESOURCE_EXHAUSTED. Quota exceeded ... 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier' "
         "Please retry in 8h21m41.92s. 'retryDelay': '30101s'")
SHORT = "429 RESOURCE_EXHAUSTED rate limit. Please retry in 12.5s."
BUSY = "503 UNAVAILABLE. This model is currently experiencing high demand."


def test_parse_retry_delay_variants():
    assert parse_retry_delay(DAILY) == 30101.0                 # retryDelay field wins
    assert parse_retry_delay("Please retry in 8h21m41.5s.") == 8 * 3600 + 21 * 60 + 41.5
    assert parse_retry_delay(SHORT) == 12.5
    assert parse_retry_delay(BUSY) == 0.0


def test_hard_vs_soft_errors():
    assert is_hard_quota_error(DAILY)
    assert not is_hard_quota_error(SHORT)       # short rate limit: normal backoff is fine
    assert not is_hard_quota_error(BUSY)        # 503 is temporary: normal retries
    assert is_quota_error(SHORT) and not is_quota_error(BUSY)


def test_guard_blocks_then_releases():
    t = [1000.0]
    g = QuotaGuard(clock=lambda: t[0])
    g.check()                                   # fresh guard lets calls through
    g.trip(DAILY)
    with pytest.raises(QuotaBlocked):
        g.check()
    t[0] += 30102                                # window passed
    g.check()


def test_trip_without_delay_uses_default():
    t = [0.0]
    g = QuotaGuard(clock=lambda: t[0])
    g.trip("429 RESOURCE_EXHAUSTED PerDay")
    assert 0 < g.remaining() <= 3600
    g.reset()
    assert g.remaining() == 0
