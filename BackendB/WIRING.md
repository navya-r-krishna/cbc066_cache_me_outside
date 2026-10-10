# Two small edits I cannot do for you (I have not seen these files)

## 1. llm/client.py  - turn on the quota circuit breaker
```python
from llm.quota_guard import quota_guard, QuotaBlocked

# a) at the top of generate_structured(), before the retry loop:
try:
    quota_guard.check()
except QuotaBlocked as qb:
    raise LLMClientError(str(qb))

# b) inside the retry loop's `except` block, right after you log "Attempt N ... failed":
if quota_guard.should_stop(str(e)):
    quota_guard.trip(str(e))
    raise LLMClientError(f"{purpose} stopped: daily Gemini quota exhausted")
```
503 and short rate limits keep their normal retries and backoff.

## 2. demo_backend_b.py  - stop printing "[OK]" when it is not OK
```python
from services.regenerate.regenerate_service import RegenerationError

# after generate_plan_questions(...):
if plan.get("source") == "demo_cache" or plan.get("status") != "ready":
    print(f"    [WARNING] Plan is {plan.get('status')} (source: {plan.get('source')}): "
          f"{plan.get('total_questions')} of {plan.get('total_requested')} budgeted questions.")
    for n in plan.get("notes", []):
        print(f"      - {n}")
else:
    print(f"    [OK] Exact budget met: {plan['total_questions']} of {plan['total_requested']} questions.")

# around the regenerate call:
try:
    new_q = await regenerate_question(...)
    print("    [OK] Regenerated:", new_q["text"])
except RegenerationError as e:
    print("    [FAILED]", e)
```

## 3. tests/test_regenerate.py
Delete `test_regenerate_fallback_preserves_original`. `tests/test_regenerate_fixes.py` replaces it.
