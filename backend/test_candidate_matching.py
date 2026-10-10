from services.candidate_profile import (
    build_candidate_profile,
    compare_candidate_to_job,
)
from services.skill_analysis import analyze_job


sample_resume = """
PROFESSIONAL SUMMARY
BCA student with experience in Python and SQL.

TECHNICAL SKILLS
Python, SQL, Pandas, Machine Learning

INTERNSHIPS
Data Analyst Intern
Example Company
Jan 2025 - Jun 2025

EDUCATION
Bachelor of Computer Applications
2023 - 2026
"""

sample_job_description = """
Data Analyst

Required skills include Python, SQL, Pandas, and Excel.
Machine Learning and Data Visualization are preferred.
The candidate must have at least 2 years of experience.
Strong communication skills are required.
"""

# Step 1: Build candidate profile
candidate = build_candidate_profile(
    resume_text=sample_resume
)

# Step 2: Analyze job description
job = analyze_job(
    sample_job_description,
    role_title="Data Analyst",
)

# Step 3: Compare candidate against job
comparison = compare_candidate_to_job(
    candidate,
    job,
    job_description=sample_job_description,
)

# Step 4: Display results
print("\n========== CANDIDATE PROFILE ==========")
print("Skills:", candidate["skills"])
print("Candidate type:", candidate["candidate_type"])

print("\n========== JOB ANALYSIS ==========")
print("Role:", job["role_title"])
print("Low information:", job["low_info"])
print(
    "Required skills:",
    [skill["name"] for skill in job["weighted_skills"]],
)

print("\n========== MATCHING RESULTS ==========")
print("Matched skills:")
for skill in comparison["matched_skills"]:
    print(f"  - {skill['name']} (weight: {skill['weight']})")

print("\nMissing skills:")
for skill in comparison["missing_skills"]:
    print(f"  - {skill['name']} (weight: {skill['weight']})")

print("\nStrengths:", comparison["strengths"])
print("Skill gaps:", comparison["gaps"])
print("Matched skill count:", comparison["matched_skill_count"])
print("Missing skill count:", comparison["missing_skill_count"])
print(
    "Skill coverage:",
    f"{comparison['skill_coverage_percentage']}%",
)
print("Warnings:", comparison["warnings"])

print("Factor scores:", comparison["factor_scores"])
print("Overall score:", comparison["overall_score"])
print("Candidate band:", comparison["candidate_band"])
print("Provisional:", comparison["score_is_provisional"])
print("Experience breakdown:", comparison["experience_breakdown"])