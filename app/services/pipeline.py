"""LangGraph multi-step AI pipeline for Job Dhundo.

Orchestrates the full user onboarding flow:
  Resume Upload → LLM Parse → Career Recommend → Job Search & Match → ATS Score

Each node is an independent step that can be retried or run individually.
State flows through the graph as a TypedDict.
"""

import logging
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.ats_scorer import score_resume
from app.services.career_recommender import recommend_roles
from app.services.job_search import rank_jobs, search_jobs
from app.services.resume_parser import parse_resume_with_llm

logger = logging.getLogger(__name__)


# --- Pipeline State ---

class PipelineState(TypedDict, total=False):
    """State that flows through the LangGraph pipeline."""
    # Input
    user_id: str
    resume_file_path: str
    location_preference: str | None
    remote_preference: str | None

    # After resume parsing
    raw_text: str
    skills: list[str]
    experience: list[dict]
    education: list[dict]
    total_experience_years: float
    summary: str

    # After career recommendation
    recommendations: list[dict]
    selected_role: str

    # After job search
    matched_jobs: list[dict]

    # After ATS scoring
    ats_result: dict

    # Error tracking
    errors: list[str]


# --- Pipeline Nodes ---

async def parse_resume_node(state: PipelineState) -> dict:
    """Node 1: Parse the uploaded resume using LLM."""
    logger.info(f"Pipeline: Parsing resume for user {state.get('user_id')}")
    try:
        parsed = await parse_resume_with_llm(state["resume_file_path"])
        return {
            "raw_text": parsed.get("raw_text", ""),
            "skills": parsed.get("skills", []),
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
            "total_experience_years": parsed.get("total_experience_years", 0.0),
            "summary": parsed.get("summary", ""),
            "errors": state.get("errors", []),
        }
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}")
        return {"errors": state.get("errors", []) + [f"Resume parsing failed: {str(e)}"]}


async def recommend_careers_node(state: PipelineState) -> dict:
    """Node 2: Recommend career roles based on parsed resume."""
    logger.info(f"Pipeline: Recommending careers for user {state.get('user_id')}")
    skills = state.get("skills", [])
    if not skills:
        return {
            "recommendations": [],
            "errors": state.get("errors", []) + ["No skills found in resume"],
        }

    try:
        recs = await recommend_roles(
            user_skills=skills,
            education=state.get("education"),
            experience=state.get("experience"),
        )
        # Auto-select the top role
        selected = recs[0]["job_role"] if recs else "Software Developer"
        return {
            "recommendations": recs,
            "selected_role": selected,
        }
    except Exception as e:
        logger.error(f"Career recommendation failed: {e}")
        return {
            "recommendations": [],
            "selected_role": "Software Developer",
            "errors": state.get("errors", []) + [f"Career recommendation failed: {str(e)}"],
        }


async def search_jobs_node(state: PipelineState) -> dict:
    """Node 3: Search and rank jobs for the selected role."""
    logger.info(f"Pipeline: Searching jobs for role '{state.get('selected_role')}'")
    role = state.get("selected_role", "Software Developer")
    skills = state.get("skills", [])
    location = state.get("location_preference")
    remote = state.get("remote_preference") == "remote"

    try:
        raw_jobs = await search_jobs(
            query=f"{role} fresher entry level",
            location=location,
            remote_only=remote,
        )
        ranked = rank_jobs(raw_jobs, skills, location)
        return {"matched_jobs": ranked}
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        return {
            "matched_jobs": [],
            "errors": state.get("errors", []) + [f"Job search failed: {str(e)}"],
        }


async def ats_score_node(state: PipelineState) -> dict:
    """Node 4: Score the resume for the selected role."""
    logger.info(f"Pipeline: ATS scoring for role '{state.get('selected_role')}'")
    raw_text = state.get("raw_text", "")
    role = state.get("selected_role")

    if not raw_text:
        return {"ats_result": {"score": 0, "suggestions": ["No resume text available"]}}

    try:
        result = await score_resume(raw_text, role)
        return {"ats_result": result}
    except Exception as e:
        logger.error(f"ATS scoring failed: {e}")
        return {
            "ats_result": {"score": 0, "suggestions": ["Scoring failed"]},
            "errors": state.get("errors", []) + [f"ATS scoring failed: {str(e)}"],
        }


# --- Conditional edges ---

def should_continue_after_parse(state: PipelineState) -> str:
    """Only proceed to career recommendation if we have skills."""
    if state.get("skills"):
        return "recommend"
    return "end"


def should_search_jobs(state: PipelineState) -> str:
    """Only search jobs if we have recommendations."""
    if state.get("recommendations"):
        return "search"
    return "score"  # Skip to scoring even without job search


# --- Build the graph ---

def build_pipeline() -> StateGraph:
    """Construct the LangGraph pipeline.

    Flow:
        parse_resume → [has skills?]
            → recommend_careers → search_jobs → ats_score → END
            → END (if no skills extracted)
    """
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node("parse_resume", parse_resume_node)
    workflow.add_node("recommend_careers", recommend_careers_node)
    workflow.add_node("search_jobs", search_jobs_node)
    workflow.add_node("ats_score", ats_score_node)

    # Set entry point
    workflow.set_entry_point("parse_resume")

    # Conditional: after parsing, check if we have skills
    workflow.add_conditional_edges(
        "parse_resume",
        should_continue_after_parse,
        {"recommend": "recommend_careers", "end": END},
    )

    # Conditional: after recommendation, check if we should search
    workflow.add_conditional_edges(
        "recommend_careers",
        should_search_jobs,
        {"search": "search_jobs", "score": "ats_score"},
    )

    # Linear: search → score → end
    workflow.add_edge("search_jobs", "ats_score")
    workflow.add_edge("ats_score", END)

    return workflow


# --- Compiled pipeline (singleton) ---

_compiled_pipeline = None


def get_pipeline():
    """Get the compiled LangGraph pipeline (cached)."""
    global _compiled_pipeline
    if _compiled_pipeline is None:
        _compiled_pipeline = build_pipeline().compile()
    return _compiled_pipeline


async def run_full_pipeline(
    user_id: str,
    resume_file_path: str,
    location_preference: str | None = None,
    remote_preference: str | None = None,
) -> PipelineState:
    """Execute the full onboarding pipeline.

    Returns the final state with all extracted data, recommendations,
    matched jobs, and ATS score.
    """
    pipeline = get_pipeline()

    initial_state: PipelineState = {
        "user_id": user_id,
        "resume_file_path": resume_file_path,
        "location_preference": location_preference,
        "remote_preference": remote_preference,
        "errors": [],
    }

    result = await pipeline.ainvoke(initial_state)
    return result
