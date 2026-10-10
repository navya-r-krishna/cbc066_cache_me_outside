import os
import sys
import asyncio
from bson import ObjectId

# Ensure project root and Backend directory are in sys.path so services and db modules can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "Backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from db import connect_to_mongo, close_mongo_connection, get_database
from services.export import generate_plan_pdf

mock_plan = {
    "questions": [
        {
            "competency": "Data Engineering",
            "skill": "SQL",
            "difficulty": "medium",
            "question": "How do you optimize a slow-running SQL query using indexes?",
            "rationale": "Tests SQL query optimization skills.",
            "key_points": ["Index types", "EXPLAIN ANALYZE"],
            "status": "accepted"
        },
        {
            "competency": "Data Engineering",
            "skill": "Python",
            "difficulty": "easy",
            "question": "What is the difference between shallow copy and deep copy?",
            "rationale": "Tests Python core memory concepts.",
            "key_points": ["copy.copy vs copy.deepcopy"],
            "status": "accepted"
        }
    ]
}

async def test_pdf_export():
    await connect_to_mongo()
    db = get_database()
    
    # Fetch any existing plan from MongoDB or fallback to mock_plan
    plan = await db["interview_plans"].find_one()
    if not plan:
        print("No existing plan found in MongoDB, using mock plan for test.")
        plan = mock_plan
    else:
        print(f"Generating PDF for MongoDB Plan ID: {plan['_id']}...")

    pdf_bytes = generate_plan_pdf(plan, candidate_name="John Doe", job_title="Python Engineer")
    
    # Save to disk to verify output
    output_filename = "test_plan_output.pdf"
    with open(output_filename, "wb") as f:
        f.write(pdf_bytes)
        
    print(f"[OK] PDF successfully generated and saved to '{output_filename}'! ({len(pdf_bytes)} bytes)")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(test_pdf_export())