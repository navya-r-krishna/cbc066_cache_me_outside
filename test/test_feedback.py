import os
import sys
import asyncio

# Ensure project root and Backend directory are in sys.path so services and db modules can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "Backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db import connect_to_mongo, close_mongo_connection
from services.feedback import log_feedback_action, get_candidate_question_history


async def run_tests():
    print("Connecting to MongoDB for testing...")
    await connect_to_mongo()

    test_plan_id = "650000000000000000000001"
    test_candidate_id = "cand_test_999"

    print("\n--- Test 1: Logging Feedback Action ---")
    log_result = await log_feedback_action(
        plan_id=test_plan_id,
        question_idx=0,
        question_text="Explain Python GIL and memory management.",
        action="reject",
        hint="Too conceptual, need practical scenario."
    )
    print("Feedback Log Result:")
    print(f"ID: {log_result.get('_id')}")
    print(f"Action: {log_result.get('action')}")
    print(f"Hint: {log_result.get('hint')}")

    print("\n--- Test 2: Retrieving Candidate Question History ---")
    history = await get_candidate_question_history(candidate_id=test_candidate_id)
    print(f"Retrieved {len(history)} past question history items for candidate '{test_candidate_id}':")
    for idx, item in enumerate(history, 1):
        print(f"  {idx}. [{item.get('source')}] {item.get('question')}")

    await close_mongo_connection()
    print("\nMongoDB connection closed. Tests complete!")


if __name__ == "__main__":
    asyncio.run(run_tests())