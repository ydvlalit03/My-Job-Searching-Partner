"""Career recommendation engine — LLM-powered with keyword fallback.

Primary: LLM analyzes skills + education + experience to recommend roles
         with market-aware reasoning.
Fallback: Keyword-based Jaccard similarity matching.
"""

import logging

from app.services.llm_client import recommend_roles_llm

logger = logging.getLogger(__name__)

# --- Keyword-based fallback map ---

ROLE_SKILL_MAP: dict[str, list[str]] = {
    "Frontend Developer": [
        "html", "css", "javascript", "typescript", "react", "angular", "vue",
        "tailwind", "next.js", "svelte", "figma",
    ],
    "Backend Developer": [
        "python", "java", "node.js", "express", "django", "flask", "fastapi",
        "spring", "sql", "postgresql", "mysql", "rest api", "graphql",
    ],
    "Full Stack Developer": [
        "html", "css", "javascript", "typescript", "react", "node.js", "python",
        "django", "fastapi", "postgresql", "mongodb", "docker", "git",
    ],
    "Data Analyst": [
        "python", "sql", "excel", "power bi", "tableau", "pandas", "numpy",
        "data analysis", "postgresql", "mysql",
    ],
    "Data Scientist": [
        "python", "machine learning", "deep learning", "nlp", "tensorflow",
        "pytorch", "pandas", "numpy", "sql", "data science",
    ],
    "ML Engineer": [
        "python", "machine learning", "deep learning", "tensorflow", "pytorch",
        "docker", "kubernetes", "aws", "mlflow", "data science",
    ],
    "DevOps Engineer": [
        "docker", "kubernetes", "aws", "azure", "gcp", "linux", "ci/cd",
        "git", "python", "terraform",
    ],
    "Mobile Developer": [
        "flutter", "react native", "swift", "kotlin", "java", "javascript",
        "typescript", "firebase", "git",
    ],
    "UI/UX Designer": [
        "figma", "photoshop", "html", "css", "javascript", "tailwind",
        "communication", "leadership",
    ],
    "Cloud Engineer": [
        "aws", "azure", "gcp", "docker", "kubernetes", "linux", "python",
        "ci/cd", "terraform", "git",
    ],
    "QA / Test Engineer": [
        "python", "java", "selenium", "javascript", "sql", "git", "agile",
        "ci/cd", "rest api", "linux",
    ],
    "Cybersecurity Analyst": [
        "linux", "python", "networking", "sql", "aws", "azure",
        "communication", "git",
    ],
    "Product Manager": [
        "agile", "scrum", "communication", "leadership", "project management",
        "data analysis", "sql", "figma", "excel",
    ],
    "Business Analyst": [
        "excel", "sql", "power bi", "tableau", "communication",
        "project management", "agile", "data analysis",
    ],
    "Technical Writer": [
        "communication", "html", "git", "python", "agile",
    ],
}


async def recommend_roles(
    user_skills: list[str],
    education: list[dict] | None = None,
    experience: list[dict] | None = None,
    top_n: int = 5,
    use_llm: bool = True,
) -> list[dict]:
    """Recommend top N career roles for the user.

    Uses LLM for intelligent, market-aware recommendations.
    Falls back to keyword matching if LLM is unavailable.
    """
    if use_llm:
        try:
            llm_results = await recommend_roles_llm(
                skills=user_skills,
                education=education or [],
                experience=experience or [],
            )
            # Validate and normalize LLM output
            validated: list[dict] = []
            for r in llm_results[:top_n]:
                validated.append({
                    "job_role": r.get("job_role", "Unknown"),
                    "match_score": min(100.0, max(0.0, float(r.get("match_score", 0)))),
                    "matched_skills": r.get("matched_skills", []),
                    "missing_skills": r.get("missing_skills", []),
                    "reasoning": r.get("reasoning", ""),
                })
            if validated:
                return validated
        except Exception as e:
            logger.warning(f"LLM career recommendation failed, using fallback: {e}")

    return _recommend_roles_keyword(user_skills, top_n)


def _recommend_roles_keyword(user_skills: list[str], top_n: int = 5) -> list[dict]:
    """Keyword-based Jaccard similarity fallback."""
    user_skill_set = {s.lower().strip() for s in user_skills}
    results: list[dict] = []

    for role, role_skills in ROLE_SKILL_MAP.items():
        role_skill_set = {s.lower() for s in role_skills}
        matched = user_skill_set & role_skill_set
        missing = role_skill_set - user_skill_set
        score = len(matched) / (len(role_skill_set) + 1e-6)
        results.append({
            "job_role": role,
            "match_score": round(score * 100, 1),
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n]
