import os
import sys

# Add project root and Backend directory to sys.path so services and config modules can be found
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "Backend")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sentence_transformers import SentenceTransformer
from services.dedup import is_duplicate, cosine_similarity

print("Loading SentenceTransformer model ('all-MiniLM-L6-v2')...")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Setup mock existing question bank
existing_questions = [
    {
        "question": "How do you optimize a slow-running SQL query using indexes?",
        "skill": "SQL",
        "difficulty": "medium"
    },
    {
        "question": "What is the difference between shallow copy and deep copy in Python?",
        "skill": "Python",
        "difficulty": "easy"
    }
]

# Test 1: Clear duplicate (reworded version of SQL query)
reworded_sql = "What steps would you take to speed up slow SQL database queries with indexing?"
is_dup_1, match_1, score_1 = is_duplicate(reworded_sql, existing_questions, model=model, threshold=0.85)

print("\n----------------------------------------")
print("--- Test 1: Reworded Duplicate Check ---")
print(f"Is Duplicate: {is_dup_1}")
print(f"Similarity Score: {score_1}")
print(f"Matched Question: {match_1['question'] if match_1 else 'None'}")
print("----------------------------------------")

# Test 2: Distinct new question
new_question = "How do you handle missing values in Pandas DataFrames?"
is_dup_2, match_2, score_2 = is_duplicate(new_question, existing_questions, model=model, threshold=0.85)

print("\n----------------------------------------")
print("--- Test 2: Distinct Question Check ---")
print(f"Is Duplicate: {is_dup_2}")
print(f"Similarity Score: {score_2}")
print(f"Matched Question: {match_2['question'] if match_2 else 'None'}")
print("----------------------------------------\n")