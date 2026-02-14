"""ATS resume scoring engine — LLM-powered with rule-based fallback.

Primary: LLM evaluates resume like a real recruiter/ATS system.
Fallback: Deterministic rule-based scoring.
"""

import logging
import re

from app.services.llm_client import score_resume_llm

logger = logging.getLogger(__name__)

ACTION_VERBS = [
    "achieved", "analyzed", "built", "collaborated", "created", "delivered",
    "designed", "developed", "drove", "enhanced", "established", "executed",
    "generated", "implemented", "improved", "increased", "integrated",
    "launched", "led", "managed", "optimized", "orchestrated", "reduced",
    "resolved", "spearheaded", "streamlined", "supervised", "transformed",
]

ROLE_KEYWORDS: dict[str, list[str]] = {
    "Frontend Developer": [
        "react", "javascript", "typescript", "html", "css", "responsive",
        "component", "ui", "ux", "webpack", "api", "state management",
    ],
    "Backend Developer": [
        "api", "database", "sql", "python", "java", "microservices",
        "rest", "authentication", "server", "scalable", "performance",
    ],
    "Full Stack Developer": [
        "frontend", "backend", "api", "database", "deployment", "full stack",
        "react", "node", "python", "docker", "ci/cd",
    ],
    "Data Analyst": [
        "analysis", "dashboard", "sql", "python", "excel", "visualization",
        "insights", "metrics", "reporting", "data",
    ],
    "Data Scientist": [
        "machine learning", "model", "python", "statistics", "prediction",
        "classification", "regression", "nlp", "deep learning", "feature engineering",
    ],
}

DEFAULT_KEYWORDS = [
    "project", "team", "developed", "implemented", "built", "designed",
    "managed", "improved", "analyzed", "created", "results",
]


async def score_resume(
    text: str,
    target_role: str | None = None,
    use_llm: bool = True,
) -> dict:
    """Score a resume for ATS compatibility.

    Uses LLM for deep, context-aware analysis.
    Falls back to rule-based scoring if LLM fails.
    """
    if use_llm and target_role:
        try:
            llm_result = await score_resume_llm(text, target_role)

            # Validate score bounds
            llm_result["score"] = min(100, max(0, int(llm_result.get("score", 0))))
            llm_result["keyword_score"] = min(40, max(0, int(llm_result.get("keyword_score", 0))))
            llm_result["format_score"] = min(20, max(0, int(llm_result.get("format_score", 0))))
            llm_result["achievement_score"] = min(20, max(0, int(llm_result.get("achievement_score", 0))))

            # Ensure required fields exist
            llm_result.setdefault("missing_keywords", [])
            llm_result.setdefault("suggestions", [])
            llm_result.setdefault("action_verbs_found", [])
            llm_result.setdefault("action_verbs_missing", [])

            return llm_result

        except Exception as e:
            logger.warning(f"LLM ATS scoring failed, using rule-based fallback: {e}")

    return _score_resume_rules(text, target_role)


def _score_resume_rules(text: str, target_role: str | None = None) -> dict:
    """Deterministic rule-based ATS scoring fallback."""
    text_lower = text.lower()
    words = text_lower.split()

    # 1. Keyword presence (40 points)
    keywords = ROLE_KEYWORDS.get(target_role or "", DEFAULT_KEYWORDS)
    found_keywords = [kw for kw in keywords if kw in text_lower]
    missing_keywords = [kw for kw in keywords if kw not in text_lower]
    keyword_score = min(40, int((len(found_keywords) / max(len(keywords), 1)) * 40))

    # 2. Action verbs (20 points)
    verbs_found = [v for v in ACTION_VERBS if v in text_lower]
    verbs_missing = [v for v in ACTION_VERBS[:10] if v not in text_lower]
    verb_score = min(20, len(verbs_found) * 3)

    # 3. Quantified achievements (20 points)
    quant_pattern = r"\d+[%+]|\$\d+|\d+\s*(users|clients|projects|customers|team|members|revenue)"
    quantified = re.findall(quant_pattern, text_lower)
    achievement_score = min(20, len(quantified) * 5)

    # 4. Format & length (20 points)
    word_count = len(words)
    format_score = 0
    if 200 <= word_count <= 800:
        format_score += 10
    elif word_count < 200:
        format_score += 3
    else:
        format_score += 5

    section_headers = ["experience", "education", "skills", "projects", "summary"]
    headers_found = sum(1 for h in section_headers if h in text_lower)
    format_score += min(10, headers_found * 2)

    total_score = keyword_score + verb_score + achievement_score + format_score

    suggestions: list[str] = []
    if keyword_score < 25:
        suggestions.append(f"Add more role-specific keywords: {', '.join(missing_keywords[:5])}")
    if verb_score < 10:
        suggestions.append(f"Use more action verbs like: {', '.join(verbs_missing[:5])}")
    if achievement_score < 10:
        suggestions.append("Quantify your achievements (e.g., 'Improved load time by 30%')")
    if word_count < 200:
        suggestions.append("Your resume is too short. Add more detail about your projects and skills.")
    elif word_count > 800:
        suggestions.append("Consider trimming your resume to keep it concise (under 2 pages).")
    if headers_found < 3:
        suggestions.append("Add clear section headers: Experience, Education, Skills, Projects")

    return {
        "score": total_score,
        "keyword_score": keyword_score,
        "format_score": format_score,
        "achievement_score": achievement_score,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
        "action_verbs_found": verbs_found,
        "action_verbs_missing": verbs_missing,
    }
