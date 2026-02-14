"""Daily roadmap generation — LLM-personalized with template fallback."""

import logging
from datetime import date, timedelta

from app.services.llm_client import generate_personalized_roadmap

logger = logging.getLogger(__name__)


async def generate_daily_roadmap(
    target_role: str,
    skills: list[str] | None = None,
    experience_years: float = 0.0,
    total_days: int = 7,
    start_date: date | None = None,
    use_llm: bool = True,
) -> list[dict]:
    """Generate a structured daily action plan.

    Uses LLM for personalized, context-aware planning.
    Falls back to template-based generation.
    """
    if start_date is None:
        start_date = date.today()

    if use_llm and skills:
        try:
            llm_plan = await generate_personalized_roadmap(
                target_role=target_role,
                skills=skills,
                experience_years=experience_years,
                days=total_days,
            )
            # Map LLM output to our schema with actual dates
            entries: list[dict] = []
            for i, item in enumerate(llm_plan[:total_days]):
                current_date = start_date + timedelta(days=i)
                entries.append({
                    "date": current_date.isoformat(),
                    "jobs_to_apply": int(item.get("jobs_to_apply", 5)),
                    "referrals_to_send": int(item.get("referrals_to_send", 3)),
                    "recruiters_to_connect": int(item.get("recruiters_to_connect", 2)),
                    "daily_tips": {
                        "focus": item.get("focus", f"Day {i + 1}"),
                        "tasks": item.get("tasks", []),
                    },
                })
            if entries:
                return entries
        except Exception as e:
            logger.warning(f"LLM roadmap generation failed, using template: {e}")

    return _generate_template_roadmap(target_role, total_days, start_date)


def _generate_template_roadmap(
    target_role: str,
    total_days: int,
    start_date: date,
) -> list[dict]:
    """Template-based fallback roadmap."""
    roadmap: list[dict] = []
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        day_num = day_offset + 1
        is_weekend = current_date.weekday() >= 5

        if is_weekend:
            entry = {
                "date": current_date.isoformat(),
                "jobs_to_apply": 3,
                "referrals_to_send": 1,
                "recruiters_to_connect": 1,
                "daily_tips": {
                    "focus": "Weekend Review",
                    "tasks": [
                        "Review applications sent this week",
                        "Update resume based on feedback",
                        f"Research 3 companies hiring for {target_role}",
                    ],
                },
            }
        else:
            entry = {
                "date": current_date.isoformat(),
                "jobs_to_apply": 5 + (day_num % 3),
                "referrals_to_send": 3,
                "recruiters_to_connect": 2,
                "daily_tips": {
                    "focus": _get_daily_focus(day_num),
                    "tasks": _get_daily_tasks(day_num, target_role),
                },
            }
        roadmap.append(entry)

    return roadmap


def _get_daily_focus(day: int) -> str:
    focuses = [
        "Mass Apply Day", "Networking Day", "Skill Polish Day",
        "LinkedIn Outreach Day", "Portfolio Day",
    ]
    return focuses[(day - 1) % len(focuses)]


def _get_daily_tasks(day: int, role: str) -> list[str]:
    base_tasks = [
        f"Apply to top-matched {role} jobs on the platform",
        "Send personalized connection requests to recruiters",
        "Follow up on yesterday's applications",
    ]
    rotating_tasks = [
        [f"Update LinkedIn headline to target {role}", "Join 2 relevant LinkedIn groups"],
        ["Practice 3 common interview questions", "Write a cover letter template"],
        [f"Identify 5 companies actively hiring {role}s", "Set up job alerts on LinkedIn"],
        ["Update GitHub/portfolio with recent project", "Write a short blog post about a project"],
        ["Review and optimize resume keywords", "Prepare a 60-second elevator pitch"],
    ]
    return base_tasks + rotating_tasks[(day - 1) % len(rotating_tasks)]
