"""Unified LLM client using official SDKs — Google GenAI and OpenAI."""

import json

import google.generativeai as genai
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()

# --- SDK initialization ---

_gemini_configured = False
_openai_client: AsyncOpenAI | None = None


def _get_gemini_model() -> genai.GenerativeModel:
    global _gemini_configured
    if not _gemini_configured:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _gemini_configured = True
    return genai.GenerativeModel(
        model_name=settings.LLM_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            max_output_tokens=2048,
        ),
    )


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# --- Core generation functions ---


async def generate_text(prompt: str, system_prompt: str = "") -> str:
    """Generate text using the configured LLM provider."""
    if settings.LLM_PROVIDER == "openai":
        return await _call_openai(prompt, system_prompt)
    return await _call_gemini(prompt, system_prompt)


async def generate_json(prompt: str, system_prompt: str = "") -> dict | list:
    """Generate structured JSON output from LLM.

    Instructs the model to return valid JSON only.
    """
    json_instruction = (
        "\n\nIMPORTANT: Respond with valid JSON only. No markdown, no code fences, no explanation."
    )
    raw = await generate_text(prompt + json_instruction, system_prompt)

    # Strip markdown code fences if model adds them anyway
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    return json.loads(cleaned)


async def _call_gemini(prompt: str, system_prompt: str) -> str:
    model = _get_gemini_model()
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    response = await model.generate_content_async(full_prompt)
    return response.text


async def _call_openai(prompt: str, system_prompt: str) -> str:
    client = _get_openai_client()
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
    )
    return response.choices[0].message.content


# --- Domain-specific generation functions ---


async def extract_resume_structured(resume_text: str) -> dict:
    """Use LLM to extract structured data from resume text."""
    system_prompt = (
        "You are an expert resume parser. Extract structured information from resumes accurately. "
        "Be thorough — capture all skills, including soft skills and tools."
    )
    prompt = f"""Parse this resume and extract structured data.

RESUME TEXT:
{resume_text[:4000]}

Return JSON in this exact format:
{{
    "skills": ["skill1", "skill2", ...],
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "duration": "Jan 2023 - Present",
            "description": "Brief description of role"
        }}
    ],
    "education": [
        {{
            "degree": "B.Tech in Computer Science",
            "institution": "University Name",
            "year": "2024"
        }}
    ],
    "total_experience_years": 0.5,
    "summary": "2-3 line professional summary of the candidate"
}}"""

    return await generate_json(prompt, system_prompt)


async def recommend_roles_llm(skills: list[str], education: list[dict], experience: list[dict]) -> list[dict]:
    """Use LLM to recommend career roles based on profile."""
    system_prompt = (
        "You are a career counselor specializing in tech careers for freshers in India. "
        "You understand the Indian job market, trending roles, and skill requirements."
    )
    prompt = f"""Based on this candidate profile, recommend the top 5 most suitable job roles.

SKILLS: {', '.join(skills)}
EDUCATION: {json.dumps(education)}
EXPERIENCE: {json.dumps(experience)}

Consider:
- Current market demand for these skills
- Roles suitable for freshers (0-1 years experience)
- Career growth potential
- Skill transferability

Return JSON array:
[
    {{
        "job_role": "Role Title",
        "match_score": 85.0,
        "matched_skills": ["skill1", "skill2"],
        "missing_skills": ["skill3", "skill4"],
        "reasoning": "Why this role fits"
    }}
]

Order by match_score descending. Scores should be between 0-100."""

    return await generate_json(prompt, system_prompt)


async def score_resume_llm(resume_text: str, target_role: str) -> dict:
    """Use LLM to perform deep ATS scoring analysis."""
    system_prompt = (
        "You are an ATS (Applicant Tracking System) expert and hiring manager. "
        "Score resumes critically but fairly. Be specific in suggestions."
    )
    prompt = f"""Score this resume for the role: {target_role}

RESUME:
{resume_text[:4000]}

Evaluate on these criteria:
1. Keyword presence for {target_role} (0-40 points)
2. Action verbs and impact language (0-20 points)
3. Quantified achievements (0-20 points)
4. Format, structure, and length (0-20 points)

Return JSON:
{{
    "score": 72,
    "keyword_score": 30,
    "format_score": 15,
    "achievement_score": 12,
    "missing_keywords": ["keyword1", "keyword2"],
    "suggestions": [
        "Specific actionable suggestion 1",
        "Specific actionable suggestion 2"
    ],
    "action_verbs_found": ["built", "designed"],
    "action_verbs_missing": ["optimized", "scaled"],
    "strengths": ["Good project descriptions", "Relevant skills listed"],
    "weaknesses": ["No quantified achievements", "Missing summary section"]
}}"""

    return await generate_json(prompt, system_prompt)


async def generate_referral_message(job_role: str, company_name: str, user_background: str) -> dict:
    """Generate a personalized referral/cold outreach message."""
    system_prompt = (
        "You are a career coach helping freshers write compelling cold outreach messages. "
        "Messages should be concise (under 150 words), professional, and show genuine interest."
    )
    prompt = f"""Generate a referral/cold outreach message for LinkedIn:

- Target Role: {job_role}
- Company: {company_name}
- Candidate Background: {user_background}

Return JSON:
{{
    "subject_line": "Subject for email/InMail",
    "message": "The full message body"
}}"""

    return await generate_json(prompt, system_prompt)


async def generate_personalized_roadmap(
    target_role: str,
    skills: list[str],
    experience_years: float,
    days: int = 7,
) -> list[dict]:
    """Use LLM to generate a personalized daily job search roadmap."""
    system_prompt = (
        "You are a career coach creating a structured daily job search plan. "
        "Be realistic about what a fresher can achieve in a day."
    )
    prompt = f"""Create a {days}-day job search action plan for a fresher targeting: {target_role}

Candidate has skills: {', '.join(skills[:10])}
Experience: {experience_years} years

For each day, provide:
- Specific number of jobs to apply to
- Number of referral messages to send
- Number of recruiters to connect with
- 3-5 specific actionable tasks

Return JSON array:
[
    {{
        "day": 1,
        "focus": "Theme for the day",
        "jobs_to_apply": 5,
        "referrals_to_send": 3,
        "recruiters_to_connect": 2,
        "tasks": ["Specific task 1", "Specific task 2", "Specific task 3"]
    }}
]"""

    return await generate_json(prompt, system_prompt)
