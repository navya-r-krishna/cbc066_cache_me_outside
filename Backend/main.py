
from IPython.core import application
@app.patch("/api/jobs/{job_id}/skills")
def update_job_skills(
    job_id: str,
    request: UpdateJobSkillsRequest,
) -> dict[str, Any]:
    """Update skill weights and synchronize competency groups."""
    if not ObjectId.is_valid(job_id):
        raise HTTPException(status_code=400, detail="Invalid job ID.")

    try:
        job = jobs_collection.find_one({"_id": ObjectId(job_id)})

        if not job:
            raise HTTPException(status_code=404, detail="Job not found.")

        current_skills = job.get("weighted_skills", [])

        skills_by_name = {
            skill["name"].casefold(): dict(skill)
            for skill in current_skills
        }

        # Reject duplicate skill names in the same request.
        submitted_names = [
            item.name.strip().casefold()
            for item in request.skills
        ]

        if len(submitted_names) != len(set(submitted_names)):
            raise HTTPException(
                status_code=400,
                detail="Each skill can be updated only once per request.",
            )

        # Update the requested raw weights.
        for item in request.skills:
            key = item.name.strip().casefold()

            if key not in skills_by_name:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Skill '{item.name}' was not found "
                        "in this job analysis."
                    ),
                )

            skills_by_name[key]["weight"] = item.weight

        updated_skills = list(skills_by_name.values())

        # Recalculate normalized weights across all job skills.
        normalize_weights(updated_skills)

        # Build a lookup of the updated skill records.
        updated_by_name = {
            skill["name"].casefold(): skill
            for skill in updated_skills
        }

        analysis = dict(job.get("analysis", {}))
        analysis["weighted_skills"] = updated_skills

        # Synchronize the nested competency groups.
        competency_groups = []

        for original_group in analysis.get("competency_groups", []):
            group = dict(original_group)
            refreshed_skills = []

            for original_skill in original_group.get("skills", []):
                skill_name = original_skill["name"].casefold()
                updated_skill = updated_by_name.get(skill_name)

                if updated_skill is not None:
                    refreshed_skills.append(dict(updated_skill))
                else:
                    # Preserve any group skill not present in the
                    # top-level weighted_skills list.
                    refreshed_skills.append(dict(original_skill))

            group["skills"] = refreshed_skills
            group["skill_count"] = len(refreshed_skills)
            group["total_weight"] = round(
                sum(skill["weight"] for skill in refreshed_skills),
                6,
            )
            group["total_normalized_weight"] = round(
                sum(
                    skill["normalized_weight"]
                    for skill in refreshed_skills
                ),
                6,
            )

            competency_groups.append(group)

        analysis["competency_groups"] = competency_groups

        # Refresh the summary.
        analysis["summary"] = dict(analysis.get("summary", {}))
        analysis["summary"]["normalized_weight_sum"] = round(
            sum(
                skill["normalized_weight"]
                for skill in updated_skills
            ),
            6,
        )

        # Persist both copies of the analysis.
        jobs_collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "weighted_skills": updated_skills,
                    "analysis": analysis,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )

        saved = jobs_collection.find_one({"_id": ObjectId(job_id)})

        return {
            "success": True,
            "message": "Job skill weights updated",
            "data": serialize_document(saved),
        }

    except HTTPException:
        raise

    except PyMongoError:
        logger.exception("Could not update job skills")
        raise HTTPException(
            status_code=503,
            detail=(
                "Database unavailable. "
                "Check MongoDB Atlas configuration."
            ),
        )
