# Job Dhundo

An **AI-powered job-search platform for freshers** — find the best-matching jobs, optimize your resume for ATS, and get a structured daily application roadmap. Built with FastAPI, async PostgreSQL, Google Gemini / OpenAI, and a LangGraph onboarding pipeline.

---

## Features

### Smart Resume Parsing
- Upload a PDF resume → structured extraction of skills, experience and education
- LLM-powered parsing with regex fallback, merged for maximum skill coverage

### Career Recommendation Engine
- Top 5 role suggestions based on your profile
- LLM reasoning over market demand and skill transferability, with Jaccard-similarity fallback

### Job Matching Engine
- Searches fresher-friendly jobs via RapidAPI (JSearch)
- Ranks by skill match, location fit and experience level

### ATS Resume Scoring (0–100)
- LLM scores your resume like a recruiter across keywords, action verbs, achievements and formatting
- Returns missing keywords and actionable fixes

### Daily Roadmap Generator
- Personalized daily action plan that tracks applications, referrals and recruiter connections

### One-Call Onboarding Pipeline
- Upload resume → parse → recommend roles → search jobs → ATS score, all in a single LangGraph `StateGraph` call with conditional routing and graceful error handling

---

## Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL + SQLAlchemy (async), Alembic migrations
- **AI / LLM**: Google Gemini / OpenAI, LangGraph orchestration
- **Job data**: RapidAPI (JSearch)
- **PDF**: pdfplumber
- **Auth**: JWT (PyJWT + bcrypt)
- **Deploy**: Docker + Docker Compose

---

## Quick Start

### Prerequisites

- Python 3.12+, PostgreSQL 16+

### Setup

```bash
cp .env.example .env
# Fill in GEMINI_API_KEY, RAPIDAPI_KEY, SECRET_KEY, DATABASE_URL

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d db redis      # start Postgres
python scripts/init_db.py          # create tables

uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the Swagger UI. For the full stack in one command: `docker compose up --build`.

---

## Design Notes

- **UUID primary keys** — no sequential ID leakage, multi-tenant safe
- **Async everything** — SQLAlchemy async + httpx for high concurrency
- **LLM-first with fallbacks** — every AI service degrades gracefully to rule-based logic
- **LangGraph orchestration** — composable, retryable, observable multi-step workflows
