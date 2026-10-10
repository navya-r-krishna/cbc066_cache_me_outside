import requests

url = "http://127.0.0.1:8001/api/analysis/candidate"
resume = "/Users/admin/Downloads/Banavi BG Resume.pdf"

jobs = [
    {
        "role_title": "Data Analyst Intern",
        "job_description": "We need Python, SQL, Pandas, NumPy, Excel, data visualization, and machine learning skills. Freshers are welcome."
    },
    {
        "role_title": "Java Backend Developer",
        "job_description": "We need Java, Spring Boot, Hibernate, REST API development, microservices, and PostgreSQL skills."
    }
]

for job in jobs:
    response = requests.post(
        url,
        json={**job, "resume_pdf_path": resume},
        timeout=60
    )
    print("\nROLE:", job["role_title"])
    print("STATUS:", response.status_code)

    if not response.ok:
        print(response.text[:1000])
        continue

    result = response.json()
    data = result.get("data", result)
    comparison = data.get("comparison", {})

    for key in (
        "overall_score",
        "factor_scores",
        "candidate_band",
        "skill_coverage_percentage"
    ):
        print(f"{key}: {comparison.get(key)}")

    print("Matched:", [s["name"] for s in comparison.get("matched_skills", [])])
    print("Missing:", [s["name"] for s in comparison.get("missing_skills", [])])
