"""Tests for the patched regenerate_service. Uses a stub client, so no API or schema classes needed."""
import pytest
from types import SimpleNamespace

from llm.client import LLMClientError
from services.regenerate.regenerate_service import regenerate_question, RegenerationError


class StubClient:
    model = "stub"

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    async def generate_structured(self, prompt, response_model, purpose=""):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(model_dump=lambda: dict(reply))


ORIGINAL_TEXT = "Explain the Global Interpreter Lock (GIL) and strategies for bypassing it."
ORIGINAL = {"id": "q_003", "competency": "Backend", "skill": "Python", "difficulty": "hard",
            "text": ORIGINAL_TEXT,                       # database field name; there is no "question" key
            "key_points": ["Thread contention", "Multiprocessing", "C extensions"]}
PLAN = {"id": "plan_1", "job_title": "Backend Dev", "questions": [ORIGINAL]}


def _reply(text):
    return {"skill": "Python", "difficulty": "hard", "question": text,
            "key_points": ["A concrete first point", "A concrete second point"]}


@pytest.mark.asyncio
async def test_exclusions_use_the_text_field():
    """A plan loaded from MongoDB only has 'text'. The old code read 'question' and allowed repeats."""
    client = StubClient([_reply(ORIGINAL_TEXT),
                         _reply("Design a thread-safe LRU cache with TTL support for a Python service.")])
    new = await regenerate_question(ORIGINAL, PLAN, client=client)
    assert new["text"] != ORIGINAL_TEXT
    assert client.calls == 2                       # first reply was rejected as a repeat


@pytest.mark.asyncio
async def test_feedback_logs_the_replaced_question():
    logged = []
    client = StubClient([_reply("Design a thread-safe LRU cache with TTL support for a Python service.")])
    new = await regenerate_question(ORIGINAL, PLAN, "more practical", client=client, feedback_logger=logged.append)
    row = logged[0]
    assert row["action"] == "regenerated"
    assert row["plan_id"] == "plan_1" and row["question_id"] == "q_003"
    assert row["question_text"] == ORIGINAL_TEXT          # the replaced question joins the do-not-repeat list
    assert row["new_question_text"] == new["text"]
    assert row["hint"] == "more practical"


@pytest.mark.asyncio
async def test_failure_raises_and_logs_nothing():
    logged = []
    client = StubClient([LLMClientError("Transient API Error")])
    with pytest.raises(RegenerationError):
        await regenerate_question(ORIGINAL, PLAN, client=client, feedback_logger=logged.append)
    assert logged == []


@pytest.mark.asyncio
async def test_llm_error_is_not_retried_in_a_loop():
    """The client already retries. The regenerate loop must not multiply the calls (quota)."""
    client = StubClient([LLMClientError("429 RESOURCE_EXHAUSTED"), _reply("Never used because we stop."),
                         _reply("Never used because we stop either.")])
    with pytest.raises(RegenerationError):
        await regenerate_question(ORIGINAL, PLAN, client=client)
    assert client.calls == 1
