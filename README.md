# AI-Based Interview Question Generator

**Team:** Cache Me Outside\
**Frontend:** React + Tailwind CSS\
**Backend:** FastAPI + Python\
**Database:** MongoDB Atlas

## Overview

The AI-Based Interview Question Generator helps interviewers prepare
relevant interview questions using job descriptions and candidate
resumes. It analyzes job requirements, extracts candidate skills and
information, compares candidate profiles with job requirements, and
supports an AI-assisted question-generation workflow.

The application uses a web dashboard for job details, resume uploads,
analysis review, and question review. The backend coordinates parsing,
analysis, AI services, validation, and persistence.

## Key Capabilities

### Job description analysis

-   Extracts skills mentioned in a job description.
-   Scores skills using requirement strength, mention frequency,
    position, requested experience, and role-title relevance.
-   Normalizes skill weights.
-   Records text evidence for detected skills.
-   Groups skills into competencies.
-   Flags low-information descriptions and distinguishes role-based
    fallback skills as assumptions.

### Resume and candidate analysis

-   Extracts text from supported resume documents.
-   Identifies sections and candidate information, including skills,
    education, projects, activities, and experience where available.
-   Builds a structured candidate profile.
-   Distinguishes projects and activities from professional experience.
-   Compares a candidate with job requirements to identify matched
    skills, gaps, strengths, and a match assessment.

### AI-assisted question workflow

-   Uses the Gemini API as part of the AI-assisted workflow.
-   Supports a frontend workflow for reviewing question cards and review
    controls.
-   Uses semantic similarity tooling to help identify potentially
    duplicate questions.

The precise behavior of individual question-generation and review
features depends on the final integrated implementation.

## Technology Stack

  -----------------------------------------------------------------------
  Component               Technology              Purpose
  ----------------------- ----------------------- -----------------------
  Frontend                React                   Interactive web
                                                  interface

  Styling                 Tailwind CSS            UI styling

  API backend             FastAPI                 HTTP API and
                                                  application
                                                  coordination

  Core logic              Python                  Parsing, analysis,
                                                  scoring, and validation

  Resume parsing          Marker                  Document parsing in the
                                                  planned workflow

  AI service              Gemini API              AI-assisted extraction
                                                  or question generation

  Semantic similarity     Sentence Transformers   Semantic comparison and
                                                  duplicate-detection
                                                  support

  Database                MongoDB Atlas           Persistent application
                                                  data

  Testing                 pytest                  Automated Python tests
  -----------------------------------------------------------------------

## Architecture


User
 |
 v
React + Tailwind CSS frontend
 |
 v
FastAPI application
 |
 +--> Resume parsing
 +--> Job description and skill analysis
 +--> Candidate profile and job-match analysis
 +--> Gemini-assisted workflow
 +--> Semantic similarity checks
 |
 v
MongoDB Atlas


The frontend communicates with the FastAPI backend through HTTP
endpoints. The backend invokes analysis and AI services, validates data,
and reads or writes persistent records in MongoDB Atlas.

## Backend Analysis Module

Backend A focuses on analysis and candidate-job matching.


backend/
├── config.py
├── database.py
├── main.py
├── models.py
├── requirements.txt
├── data/
│   ├── skills.json
│   └── competencies.json
├── services/
│   ├── resume_parser.py
│   ├── skill_analysis.py
│   ├── skill_matcher.py
│   └── candidate_profile.py
├── test_candidate_matching.py
└── test_candidate_profile.py


### Main responsibilities

-   `services/skill_matcher.py` --- matches skill names and aliases
    while applying safeguards for ambiguous terms.
-   `services/skill_analysis.py` --- extracts job-description skills,
    calculates weighted scores, records evidence, groups competencies,
    and flags low-information descriptions.
-   `services/resume_parser.py` --- extracts and structures resume text
    and candidate details.
-   `services/candidate_profile.py` --- builds candidate profiles and
    compares candidates with job requirements.
-   `data/skills.json` --- skill vocabulary and aliases used by the
    analysis pipeline.
-   `data/competencies.json` --- competency group definitions.
-   `database.py` --- MongoDB connection and collection access.
-   `main.py` --- FastAPI application and API endpoints.
-   `models.py` --- backend data models.
-   `config.py` --- application configuration.

### Skill weighting

The job-analysis module combines five signals:

  Signal                            Weight
  ------------------------------- --------
  Requirement level                   0.35
  Frequency                           0.25
  Position                            0.15
  Years of experience requested       0.15
  Role-title relevance                0.10

The combined score is normalized into skill weights. These weights
prioritize job requirements; they are not a guarantee of candidate
performance.

## API Endpoints

The current Backend A implementation includes:

  -----------------------------------------------------------------------------
  Method                  Endpoint                      Purpose
  ----------------------- ----------------------------- -----------------------
  `GET`                   `/`                           Root/status response

  `GET`                   `/health`                     Health and service
                                                        status

  `POST`                  `/api/analysis/candidate`     Analyze a candidate
                                                        against a job

  `POST`                  `/api/jobs`                   Create and persist a
                                                        job

  `PATCH`                 `/api/jobs/{job_id}/skills`   Update job skill
                                                        weights

  `POST`                  `/api/candidates`             Create and persist a
                                                        candidate profile
  -----------------------------------------------------------------------------

FastAPI's Swagger UI provides interactive API documentation when the
server is running.

## Prerequisites

-   Python installed
-   Access to a MongoDB Atlas cluster
-   A Gemini API key for features that call Gemini
-   Node.js and a package manager for the React frontend
-   The project repository and its dependency files

Use the versions and setup commands specified by the integrated
repository's dependency files.

## Configuration

Create a local environment file at the path expected by the backend
configuration, such as `backend/.env`.

Example placeholders:

``` dotenv
MONGODB_URI=your_mongodb_atlas_connection_string
DATABASE_NAME=your_database_name
GEMINI_API_KEY=your_gemini_api_key
```

These variable names are illustrative. Confirm the exact names against
`config.py` and the AI integration code before running the application.

**Security** - Never commit `.env` files, database credentials, or API
keys. - Keep `.env` in `.gitignore`. - Do not paste secrets into issues,
logs, screenshots, or public repositories. - Configure MongoDB Atlas
network access and database users with least privilege. - Never expose
private credentials in frontend code.

## Running the Backend

Run these commands from the repository root:

``` bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --port 8001
```

Activate the intended Python or Conda environment first. If package
installation fails, troubleshoot that environment rather than changing
the system Python installation blindly.

When the server is running: - API root: `http://127.0.0.1:8001/` -
Health endpoint: `http://127.0.0.1:8001/health` - Swagger documentation:
`http://127.0.0.1:8001/docs`

Features that depend on external services require valid configuration
and connectivity.

## Running Tests

From the repository root:

``` bash
python -m pytest backend/test_candidate_matching.py backend/test_candidate_profile.py -v
```

The current Backend A candidate-matching and candidate-profile test
suite passed **13 tests** in the development environment. Rerun the
tests after changes and before merging or demonstrating the project.

## Data and Limitations

-   The skill vocabulary and competency groups are maintained in JSON
    configuration files.
-   Skill matching uses text and aliases; context affects interpretation
    of ambiguous terms.
-   Resume extraction quality depends on document structure and whether
    it contains machine-readable text.
-   AI-generated content can be incorrect or inconsistent and should be
    reviewed by a human.
-   Match scores are decision-support signals, not objective judgments
    of a person's ability.
-   Vague job descriptions can reduce analysis reliability.
-   Database availability, API credentials, and network configuration
    affect integrated functionality.

## Suggested End-to-End Demo

1.  Start MongoDB Atlas connectivity and the backend.
2.  Open `/docs` and confirm the health endpoint responds.
3.  Create a job using a sample job description.
4.  Review detected skills, evidence, competency groups, and weights.
5.  Update one or more skill weights and verify the response.
6.  Create a candidate profile from sample resume content.
7.  Run candidate-job analysis and review matched skills, gaps, and the
    resulting assessment.
8.  Demonstrate the integrated frontend and AI-assisted question
    workflow if those services are configured and available.

Use sample or consented data for demonstrations. Avoid uploading real
personal information unless necessary and appropriately handled.

## Team Contributions

The project is being developed collaboratively. Backend A covers
job-description analysis, resume parsing, candidate profiles, skill
weighting, and candidate-job comparison. Describe other backend
components and frontend contributions according to the final integrated
implementation.

## Future Improvements

-   Expand and validate the skill vocabulary and aliases.
-   Add tests for malformed resumes, vague job descriptions, and invalid
    skill-weight updates.
-   Improve error handling for database and external AI-service
    failures.
-   Evaluate extraction and matching quality against a representative
    test set.
-   Add human review and feedback for generated questions.
-   Document deployment, environment variables, and frontend setup after
    integration.

## License

Add the license selected by the project team before public distribution.
