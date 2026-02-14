"""Job search integration via RapidAPI (JSearch)."""

import httpx

from app.core.config import get_settings

settings = get_settings()


async def search_jobs(
    query: str,
    location: str | None = None,
    remote_only: bool = False,
    page: int = 1,
    num_pages: int = 1,
) -> list[dict]:
    """Search for jobs via RapidAPI JSearch endpoint.

    Replace RAPIDAPI_BASE_URL and RAPIDAPI_HOST in .env when
    you plug in your actual API key and endpoint.
    """
    params: dict = {
        "query": query,
        "page": str(page),
        "num_pages": str(num_pages),
        "date_posted": "month",
    }
    if remote_only:
        params["remote_jobs_only"] = "true"
    if location:
        params["query"] = f"{query} in {location}"

    headers = {
        "X-RapidAPI-Key": settings.RAPIDAPI_KEY,
        "X-RapidAPI-Host": settings.RAPIDAPI_HOST,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{settings.RAPIDAPI_BASE_URL}/search",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    raw_jobs = data.get("data", [])
    return _normalize_jobs(raw_jobs)


def _normalize_jobs(raw: list[dict]) -> list[dict]:
    """Normalize RapidAPI JSearch response to our internal format."""
    jobs: list[dict] = []
    for item in raw:
        jobs.append({
            "external_job_id": item.get("job_id"),
            "title": item.get("job_title", ""),
            "company": item.get("employer_name", ""),
            "location": item.get("job_city", "") or item.get("job_country", ""),
            "is_remote": item.get("job_is_remote", False),
            "apply_url": item.get("job_apply_link", ""),
            "description": item.get("job_description", "")[:2000],  # Truncate
            "salary_range": _extract_salary(item),
        })
    return jobs


def _extract_salary(item: dict) -> str | None:
    min_sal = item.get("job_min_salary")
    max_sal = item.get("job_max_salary")
    currency = item.get("job_salary_currency", "USD")
    if min_sal and max_sal:
        return f"{currency} {min_sal:,.0f} - {max_sal:,.0f}"
    if min_sal:
        return f"{currency} {min_sal:,.0f}+"
    return None


def rank_jobs(jobs: list[dict], user_skills: list[str], location_pref: str | None = None) -> list[dict]:
    """Rank jobs by match score based on skill overlap, location, and experience fit."""
    user_skill_set = {s.lower() for s in user_skills}

    for job in jobs:
        desc_lower = (job.get("description") or "").lower()
        title_lower = (job.get("title") or "").lower()

        # Skill match (0-60)
        skill_hits = sum(1 for s in user_skill_set if s in desc_lower or s in title_lower)
        skill_score = min(60, (skill_hits / max(len(user_skill_set), 1)) * 60)

        # Location match (0-20)
        loc_score = 0
        if location_pref:
            job_loc = (job.get("location") or "").lower()
            if location_pref.lower() in job_loc:
                loc_score = 20
            elif job.get("is_remote"):
                loc_score = 15

        # Experience fit — fresher friendly (0-20)
        exp_score = 20  # Default: assume entry level
        for marker in ["5+ years", "4+ years", "3+ years", "senior", "lead", "principal"]:
            if marker in desc_lower:
                exp_score = 0
                break
        for marker in ["entry level", "fresher", "0-1 year", "junior", "intern", "graduate"]:
            if marker in desc_lower:
                exp_score = 20
                break

        job["match_score"] = round(skill_score + loc_score + exp_score, 1)
        job["match_details"] = {
            "skill_score": round(skill_score, 1),
            "location_score": loc_score,
            "experience_score": exp_score,
        }

    jobs.sort(key=lambda j: j["match_score"], reverse=True)
    return jobs[:20]
