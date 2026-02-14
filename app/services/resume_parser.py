"""Resume parser — PDF text extraction + LLM-powered structured extraction.

Strategy:
1. Extract raw text from PDF via pdfplumber
2. Run LLM extraction for accurate skill/experience/education parsing
3. Fall back to regex-based extraction if LLM fails (rate limit, API down, etc.)
"""

import logging
import re

import pdfplumber

from app.services.llm_client import extract_resume_structured

logger = logging.getLogger(__name__)


# --- PDF text extraction ---

def extract_text_from_pdf(file_path: str) -> str:
    """Extract raw text from a PDF file."""
    text_parts: list[str] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


# --- LLM-powered parsing (primary) ---

async def parse_resume_with_llm(file_path: str) -> dict:
    """Parse resume using LLM for high-accuracy extraction.

    Returns structured dict with skills, experience, education, etc.
    Falls back to regex if LLM call fails.
    """
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text.strip():
        return {
            "raw_text": "",
            "skills": [],
            "education": [],
            "experience": [],
            "total_experience_years": 0.0,
        }

    try:
        llm_result = await extract_resume_structured(raw_text)

        # Normalize LLM output to our schema
        skills = [s.lower().strip() for s in llm_result.get("skills", [])]
        experience = llm_result.get("experience", [])
        education = llm_result.get("education", [])
        total_years = float(llm_result.get("total_experience_years", 0))

        # Merge: LLM skills + regex skills (LLM might miss abbreviations, regex catches them)
        regex_skills = _extract_skills_regex(raw_text)
        all_skills = sorted(set(skills) | set(regex_skills))

        return {
            "raw_text": raw_text,
            "skills": all_skills,
            "education": education,
            "experience": experience,
            "total_experience_years": total_years,
            "summary": llm_result.get("summary", ""),
        }

    except Exception as e:
        logger.warning(f"LLM resume parsing failed, falling back to regex: {e}")
        return _parse_resume_regex(raw_text)


# --- Regex fallback parser ---

SKILL_PATTERNS: set[str] = {
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "node.js", "express", "django", "flask", "fastapi", "spring", "sql",
    "postgresql", "mysql", "mongodb", "redis", "docker", "kubernetes",
    "aws", "azure", "gcp", "git", "linux", "html", "css", "tailwind",
    "figma", "photoshop", "excel", "power bi", "tableau", "machine learning",
    "deep learning", "nlp", "tensorflow", "pytorch", "pandas", "numpy",
    "data analysis", "data science", "communication", "leadership",
    "project management", "agile", "scrum", "ci/cd", "rest api",
    "graphql", "c++", "c#", ".net", "ruby", "go", "rust", "swift",
    "kotlin", "flutter", "react native", "next.js", "svelte",
}

DEGREE_PATTERNS: list[str] = [
    r"(?i)b\.?\s?tech", r"(?i)b\.?\s?e\b", r"(?i)b\.?\s?sc",
    r"(?i)m\.?\s?tech", r"(?i)m\.?\s?sc", r"(?i)m\.?\s?ba",
    r"(?i)b\.?\s?ba", r"(?i)b\.?\s?com", r"(?i)m\.?\s?com",
    r"(?i)ph\.?\s?d", r"(?i)diploma", r"(?i)bca", r"(?i)mca",
    r"(?i)b\.?\s?des", r"(?i)m\.?\s?des",
    r"(?i)bachelor", r"(?i)master", r"(?i)associate",
]

SECTION_HEADERS_EXPERIENCE = [
    r"(?i)experience", r"(?i)work\s*history", r"(?i)employment",
    r"(?i)professional\s*experience",
]

SECTION_HEADERS_EDUCATION = [
    r"(?i)education", r"(?i)academic", r"(?i)qualification",
]


def _extract_skills_regex(text: str) -> list[str]:
    text_lower = text.lower()
    found: list[str] = []
    for skill in SKILL_PATTERNS:
        pattern = rf"\b{re.escape(skill)}\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def _extract_education_regex(text: str) -> list[dict]:
    entries: list[dict] = []
    lines = text.split("\n")
    in_education = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.search(p, stripped) for p in SECTION_HEADERS_EDUCATION):
            in_education = True
            continue
        if any(re.search(p, stripped) for p in SECTION_HEADERS_EXPERIENCE):
            in_education = False
            continue
        if in_education:
            for dp in DEGREE_PATTERNS:
                m = re.search(dp, stripped)
                if m:
                    year_match = re.search(r"(20\d{2}|19\d{2})", stripped)
                    entries.append({
                        "degree": m.group(),
                        "detail": stripped,
                        "year": year_match.group() if year_match else None,
                    })
                    break
    return entries


def _extract_experience_regex(text: str) -> list[dict]:
    entries: list[dict] = []
    lines = text.split("\n")
    in_experience = False
    current_entry: list[str] = []
    for line in lines:
        stripped = line.strip()
        if any(re.search(p, stripped) for p in SECTION_HEADERS_EXPERIENCE):
            in_experience = True
            continue
        if any(re.search(p, stripped) for p in SECTION_HEADERS_EDUCATION):
            if current_entry:
                entries.append({"detail": " ".join(current_entry)})
            in_experience = False
            continue
        if in_experience and stripped:
            date_match = re.search(
                r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}",
                stripped, re.IGNORECASE,
            )
            if date_match and current_entry:
                entries.append({"detail": " ".join(current_entry)})
                current_entry = []
            current_entry.append(stripped)
    if current_entry:
        entries.append({"detail": " ".join(current_entry)})
    return entries


def _estimate_experience_years(text: str) -> float:
    import datetime
    year_ranges = re.findall(
        r"(20\d{2}|19\d{2})\s*[-–to]+\s*(20\d{2}|19\d{2}|present|current)",
        text, re.IGNORECASE,
    )
    total = 0.0
    for start, end in year_ranges:
        s = int(start)
        e = datetime.datetime.now().year if end.lower() in ("present", "current") else int(end)
        total += max(0, e - s)
    return total


def _parse_resume_regex(raw_text: str) -> dict:
    """Regex-based fallback parser."""
    return {
        "raw_text": raw_text,
        "skills": _extract_skills_regex(raw_text),
        "education": _extract_education_regex(raw_text),
        "experience": _extract_experience_regex(raw_text),
        "total_experience_years": _estimate_experience_years(raw_text),
    }
