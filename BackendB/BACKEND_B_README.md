# InterviewIQ — Backend B: AI Interview Question Generation

Backend B is the intelligence engine of **InterviewIQ**. It transforms structured job requirements and candidate profiles into mathematically balanced, highly tailored technical interview plans using Google's Gemini models.

---

## 1. Module Responsibilities

1. **Gemini Integration**: Official `google-genai` SDK wrapper with structured Pydantic output, automated backoff retries, request timeouts, and PII-redacted logging.
2. **Difficulty Distribution**: Computes deterministic easy/medium/hard question distributions based on candidate seniority bands and optional interviewer overrides.
3. **Question Budgeting**: Employs Hare-Niemeyer (largest-remainder) rounding to proportionally distribute questions across competencies, skills, and difficulty tiers to match exact interview duration constraints.
4. **Prompt Engineering & Generation**: Role-specific, anti-injection-hardened prompts that generate deep technical challenges with 3–5 evaluation key points.
5. **Deterministic Validation**: Rigorous Pydantic schema validation, length requirements, allowed difficulty boundaries, and internal deduplication.
6. **Question Regeneration**: Interactive swapping of rejected or inappropriate questions using interviewer hints while strictly preserving competency and difficulty constraints.
7. **Caching & Fallback**: Fast in-memory and file-based caching with TTL support, plus an instant demo plan fallback (`data/demo_plan.json`) during API outages or quota limits.

---

## 2. Folder Structure

```text
├── llm/
│   ├── __init__.py
│   ├── client.py                # Official Google GenAI SDK async/sync client wrapper
│   └── prompts.py               # Prompt engineering, injection protection & Pydantic models
│
├── services/
│   ├── __init__.py
│   ├── difficulty/
│   │   ├── __init__.py
│   │   └── difficulty_service.py # Deterministic seniority & evidence difficulty calculator
│   ├── question_gen/
│   │   ├── __init__.py
│   │   ├── budget.py            # Hare-Niemeyer question budget allocator
│   │   ├── generator.py         # Main generation pipeline & rationale builder
│   │   └── cache.py             # BaseCache, InMemoryCache, FileCache & fallback loader
│   └── regenerate/
│       ├── __init__.py
│       └── regenerate_service.py # Question regeneration with interviewer hints
│
├── utils/
│   ├── __init__.py
│   └── validators.py            # Pydantic validation & deduplication logic
│
├── data/
│   ├── mock_analysis.json       # Backend A integration contract data
│   ├── sample_jobs.json         # Multi-role test profiles (Backend, React, Analyst)
│   └── demo_plan.json           # Validated pre-generated fallback interview plan
│
├── tests/
│   ├── test_client.py           # Client retry, timeout, parsing & mock tests
│   ├── test_difficulty.py       # Difficulty distribution and override tests
│   ├── test_budget.py           # Hare-Niemeyer allocation & edge cases tests
│   ├── test_generation.py       # Full generation pipeline & cache hit tests
│   ├── test_validation.py       # Pydantic schema & length validation tests
│   ├── test_regenerate.py       # Question regeneration & exclusion tests
│   └── test_cache.py            # Cache key hashing & TTL expiration tests
│
├── config.py                    # Central configuration & typed settings
├── demo_backend_b.py            # End-to-end interactive CLI demonstration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
└── BACKEND_B_README.md          # Complete documentation
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
GEMINI_TEMPERATURE=0.4
GEMINI_TIMEOUT=30
GEMINI_MAX_RETRIES=3

AVERAGE_QUESTION_MINUTES=3
GENERATION_STRATEGY=single_call
CACHE_TTL_SECONDS=3600
MAX_CONCURRENT_LLM_CALLS=1
```

---

## 4. How to Run the Demonstration

### Mock Simulation (No API key required)
Runs entirely locally with mock transport and validates every subsystem:
```bash
python demo_backend_b.py --mock
```

### Live Gemini Execution
Connects directly to Google Gemini using your configured API key:
```bash
python demo_backend_b.py
```

---

## 5. How to Run the Test Suite

Execute the entire test suite using `pytest`:
```bash
python -m pytest tests/ -v
```

All 38 tests run completely offline without making external network calls.

---

## 6. MongoDB Database Schema & Collection Alignment

Backend B directly consumes and produces documents aligned 1-to-1 with the system's 5 MongoDB collections:

### 1. `job_descriptions` (Written by Backend A job analysis)
| Field | Type | Backend B Usage |
|---|---|---|
| `id` | `string` | Unique JD ID. Copied into generated `interview_plans.job_id`. |
| `title` | `string` | Role title (e.g. "Data Analyst"). Placed in Prompt A context. |
| `raw_text` | `string` | Original job text parsed by Marker. Used for fallback and context. |
| `skills` | `array[object]` | Extracted role skills with weights. |
| `competencies` | `array[object]` | Structured competency trees used by `budget.py` for slot allocation. |
| `experience_level`| `string` | `"fresher"`, `"mid"`, or `"senior"`. Used to calibrate difficulty baseline. |
| `low_info` | `boolean` | When `True`, triggers auto-synthesis of missing competencies with `assumed: True` flags. |
| `unknown_terms` | `array[string]`| Non-dictionary terms tracked for audit. |
| `created_at` | `datetime` | Creation timestamp. |

### 2. `candidates` (Written by Backend A resume parsing)
| Field | Type | Backend B Usage |
|---|---|---|
| `id` | `string` | Unique candidate ID. Copied into `interview_plans.candidate_id`. |
| `name` | `string` | Display name. **Never sent to LLM** (anti-bias / PII protection). |
| `resume_md` | `string` | Marker-parsed resume markdown. |
| `experience_years`| `number` | Used in seniority band calculation. |
| `education` | `array[string]`| Educational degrees. |
| `skills` | `array[string]`| Skills verified from resume. |
| `is_fresher` | `boolean` | If `True`, locks difficulty baseline to beginner mix (50/35/15). |
| `score` | `number` | Candidate score (0 to 100). |
| `band` | `string` | `"beginner"`, `"intermediate"`, or `"advanced"`. Sets base difficulty mix. |
| `strengths` | `array[string]`| High-evidence skills prioritized for hard/medium questions. |
| `gaps` | `array[string]`| Missing skills prioritized for foundational/easy questions. |
| `history` | `array[object]`| Past questions (`question`, `answer`, `plan_id`). Automatically parsed into prompt exclusions to prevent repeat questions. |
| `created_at` | `datetime` | Creation timestamp. |

### 3. `interview_plans` (Main collection, written by Backend C assembly)
| Field | Type | Backend B Population |
|---|---|---|
| `id` | `string` | Unique plan ID. |
| `job_id` | `string` | Populated from `job_descriptions.id`. |
| `candidate_id` | `string` | Populated from `candidates.id`. |
| `job_title` | `string` | Copied for quick UI display. |
| `candidate_name` | `string` | Copied for quick UI display. |
| `settings` | `object` | `{interview_minutes, difficulty, difficulty_mix}`. |
| `status` | `string` | `"ready"` (complete budget met) or `"partial"` (shortfall). |
| `note` | `string` | Explanation note (e.g. `"Only 4 of 5 questions could be generated"`). |
| `questions` | `array[object]`| List of embedded question objects (see structure below). |
| `coverage` | `array[object]`| Breakdown of questions allocated per competency and skill. |
| `created_at` | `datetime` | Creation timestamp. |

#### Embedded `questions` item format:
```json
{
  "id": "q_001",
  "competency": "Backend Development",
  "skill": "Python",
  "difficulty": "hard",
  "text": "How would you identify and resolve memory leaks in a Python service?",
  "question": "How would you identify and resolve memory leaks in a Python service?",
  "key_points": [
    "Profile memory with tracemalloc and objgraph",
    "Inspect gc cyclic reference collection",
    "Analyze C extension refcounts"
  ],
  "rationale": "Tests Python under Backend Development: required skill (30% role weighting), with strong candidate evidence. Calibrated at hard difficulty.",
  "status": "pending",
  "assumed": false,
  "embedding": [0.012, -0.045, "... 384 dimensions computed by Backend C ..."],
  "response": null,
  "score": null,
  "follow_ups": []
}
```

### 4. `feedback` (Action log, written by Backend C review routes)
| Field | Type | Backend B Integration |
|---|---|---|
| `id` | `string` | Unique log entry ID. |
| `plan_id` | `string` | Targeted plan ID. |
| `question_id` | `string` | Replaced/reviewed question ID. |
| `action` | `string` | `"accepted"`, `"rejected"`, `"pending"`, or `"regenerated"`. |
| `hint` | `string` | Optional interviewer hint (e.g. `"Make it more practical with async"`). |
| `question_text` | `string` | The question text at the time. Replaced questions feed exclusion lists. |
| `created_at` | `datetime` | Action timestamp. |

### 5. `cache` (Written by Backend B for zero-latency repeat demos)
| Field | Type | Backend B Population |
|---|---|---|
| `id` | `string` | SHA-256 hash of `(job, band, minutes, model, exclusions)`. |
| `result` | `object` | The cached generation response payload. |
| `created_at` | `datetime` | Cache creation timestamp with TTL support. |

### Backend C Adapters:
1. **Deduplication Adapter**: Pass Backend C's semantic deduplication function:
   ```python
   def is_duplicate(text: str, existing_texts: list[str]) -> bool: ...
   
   plan = await generate_plan_questions(..., dedup=is_duplicate)
   ```
2. **MongoDB Cache Adapter**: Subclass `BaseCache` to replace the default in-memory cache:
   ```python
   from services.question_gen.cache import BaseCache
   
   class MongoCache(BaseCache):
       def get(self, key: str): ...
       def set(self, key: str, value: dict, ttl_seconds: int = None): ...
       def delete(self, key: str): ...
       def clear(self): ...
   ```
3. **Feedback Collection**: Pass a callback to receive regeneration logs:
   ```python
   def log_feedback(data: dict):
       # Save to MongoDB feedback collection
       ...

   new_q = await regenerate_question(..., feedback_logger=log_feedback)
   ```

---

## 7. Question Regeneration Workflow

When an interviewer dislikes a question or wants an alternative angle:
1. The question's skill, competency, and difficulty are locked.
2. An exclusion list is built including:
   - All currently active questions in the plan
   - The question being replaced
   - Any previously rejected questions
   - The candidate's past interview question history
3. An optional interviewer hint (e.g., *"Make it more practical with async"*) is injected into Prompt B.
4. Gemini generates a single replacement question.
5. The replacement is validated and checked against the duplicate detector.
6. If regeneration succeeds, the new question is returned with a unique ID and feedback is dispatched to Backend C. If all retries fail, the original question is preserved safely without crashing.

---

## 8. Caching & High Availability

- **Input Normalization**: SHA-256 hash computed over job title, competencies, weights, candidate band, interview duration, model, difficulty override, strategy, candidate strengths/gaps, and prompt version.
- **PII Scrubbing**: Candidate names, resumes, emails, and phone numbers are never included in cache keys, prompts, or logs.
- **Pinned Gemini Model**: Always pin a specific model from Google AI Studio (e.g. `gemini-3.8-flash` in `GEMINI_MODEL`) rather than generic aliases to ensure predictable quota and behavior.
- **Outage Fallback**: If Gemini encounters rate limits (429) or service outages (503), Backend B automatically loads the pre-validated `data/demo_plan.json` with an explicit `source: "demo_cache"` tag and informational notes so live demos never fail.
