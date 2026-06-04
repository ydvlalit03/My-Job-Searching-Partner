<div align="center">

# 🧭 Job Dhundo

### An AI-powered job-search platform for freshers — match jobs, beat the ATS, and get a daily roadmap

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-pipeline-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_/_OpenAI-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 📖 Overview

Job hunting as a fresher is overwhelming: which roles fit you, which jobs are worth applying to, why your resume keeps getting auto-rejected, and what to actually *do* each day. **Job Dhundo** answers all four with one AI pipeline.

Upload your resume and the platform parses it, recommends the best-fit roles, finds and ranks fresher-friendly jobs, scores your resume against ATS systems with concrete fixes, and generates a personalized **daily application roadmap** that tracks your applications, referrals and recruiter connections. The entire onboarding flow can run in a **single LangGraph-orchestrated API call**.

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Architecture](#-architecture)
- [The LangGraph pipeline](#-the-langgraph-pipeline)
- [Database schema](#-database-schema)
- [API reference](#-api-reference)
- [Installation](#-installation)
- [Environment variables](#-environment-variables)
- [Project structure](#-project-structure)
- [Design decisions](#-design-decisions)
- [Roadmap](#-roadmap)

---

## ✨ Features

### 1. 📄 Smart Resume Parsing
- Upload a PDF resume → structured extraction of **skills, experience and education**
- LLM-powered parsing with a **regex fallback** for reliability
- Merges LLM + regex output for maximum skill coverage

### 2. 🎯 Career Recommendation Engine
- Top **5 role suggestions** tailored to your profile
- LLM reasoning weighs market demand, skill transferability and growth
- Falls back to **keyword-based Jaccard similarity** when the LLM is unavailable

### 3. 🔍 Job Matching Engine
- Searches fresher-friendly jobs via **RapidAPI (JSearch)**
- Ranks by skill match, location fit and experience level
- Returns the top 20 with detailed match scores

### 4. 📊 ATS Resume Scoring (0–100)
- The LLM evaluates your resume **like a real recruiter**
- Scores 4 dimensions: keywords, action verbs, achievements, formatting
- Returns **missing keywords** and actionable improvement suggestions

### 5. 🗓️ Daily Roadmap Generator
- LLM-personalized daily action plan
- Tracks applications, referrals and recruiter connections
- Auto-completes a day when all targets are hit

### 6. 💬 Referral Message Generator
- LLM-generated cold outreach for LinkedIn
- Personalized to the target role, company and your background

### 7. ⚡ One-Call Onboarding Pipeline
- Upload resume → parse → recommend roles → search jobs → ATS score
- All in a **single API call** powered by a LangGraph `StateGraph` with conditional routing and graceful per-node error handling

---

## 🛠️ Tech stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.12) |
| **Database** | PostgreSQL + SQLAlchemy (async) |
| **AI / LLM** | Google Gemini SDK / OpenAI SDK |
| **Orchestration** | LangGraph (multi-step AI workflows) |
| **Job search** | RapidAPI (JSearch) |
| **PDF parsing** | pdfplumber |
| **Auth** | JWT (PyJWT + bcrypt) |
| **Migrations** | Alembic |
| **Containerization** | Docker + Docker Compose |

---

## 🏗️ Architecture

```
        ┌──────────────┐      ┌──────────────────────────────────────────┐
client ─▶│ FastAPI (v1) │─────▶│ services/                                 │
        └──────────────┘      │  resume_parser · career_recommender ·     │
              │               │  ats_scorer · job_search · roadmap_gen ·  │
              │               │  pipeline (LangGraph) · llm_client        │
              ▼               └──────────────────────────────────────────┘
   JWT auth + async deps                     │
              │                              ▼
              └────────▶ PostgreSQL (async SQLAlchemy, JSONB columns)
```

Every AI service is **LLM-first with a deterministic fallback**, so the platform keeps working even when the model or an external API is down.

---

## 🔄 The LangGraph pipeline

```
                        ┌─────────────────┐
                        │  parse_resume    │
                        │  (LLM + regex)   │
                        └────────┬────────┘
                              [has skills?]
                            yes /      \ no
                               /        └──▶ END
                  ┌───────────────────┐
                  │ recommend_careers  │
                  │  (LLM + keyword)   │
                  └────────┬──────────┘
                     [has recommendations?]
                       yes /        \ no
                          /          \
              ┌──────────────────┐   ┌──────────────┐
              │   search_jobs     │   │  ats_score    │
              │ (RapidAPI + rank) │   │ (LLM + rules) │
              └────────┬─────────┘   └──────┬───────┘
                       └────────┬───────────┘
                          ┌──────────────┐
                          │  ats_score    │
                          └──────┬───────┘
                                END
```

---

## 🗄️ Database schema

```
┌──────────────┐     ┌───────────────────┐     ┌────────────────────────┐
│    users      │────▶│  resume_profiles   │     │ career_recommendations │
├──────────────┤     ├───────────────────┤     ├────────────────────────┤
│ id (UUID)     │     │ id (UUID)          │     │ id (UUID)              │
│ email         │     │ user_id (FK)       │     │ user_id (FK)           │
│ hashed_pass   │     │ skills[]           │     │ job_role               │
│ full_name     │     │ experience (JSONB) │     │ match_score            │
│ degree        │     │ education (JSONB)  │     │ matched_skills[]       │
│ location_pref │     │ ats_score          │     │ missing_skills[]       │
│ remote_pref   │     │ ats_feedback       │     │ is_selected            │
│ salary_exp    │     └───────────────────┘     └────────────────────────┘
└──────────────┘
        ├──────────────────────┐
┌───────────────┐      ┌─────────────────┐
│  saved_jobs    │      │ roadmap_entries  │
├───────────────┤      ├─────────────────┤
│ id · user_id   │      │ id · user_id     │
│ title · company│      │ date             │
│ match_score    │      │ jobs_to_apply    │
│ match_details  │      │ referrals_to_send│
│ status         │      │ jobs_applied     │
│ apply_url      │      │ daily_tips       │
└───────────────┘      │ is_completed     │
                       └─────────────────┘
```

---

## 🌐 API reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | register a new user |
| POST | `/api/v1/auth/login` | login → JWT token |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | current user profile |
| PATCH | `/api/v1/users/me/onboard` | set location/remote/salary preferences |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resume/upload` | upload + parse resume (PDF) |
| GET | `/api/v1/resume/profile` | get parsed resume data |
| POST | `/api/v1/resume/ats-score` | ATS score (0–100) + suggestions |

### Career
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/career/recommend` | top 5 role recommendations |
| POST | `/api/v1/career/select-roles` | select target roles |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jobs/search` | search + rank jobs |
| POST | `/api/v1/jobs/save/{index}` | save a matched job |
| GET | `/api/v1/jobs/saved` | list saved jobs |
| PATCH | `/api/v1/jobs/saved/{id}/status` | update application status |

### Roadmap
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/roadmap/generate` | generate weekly action plan |
| GET | `/api/v1/roadmap/today` | today's tasks |
| PATCH | `/api/v1/roadmap/{id}/progress` | update daily progress |
| POST | `/api/v1/roadmap/referral-message` | generate referral message |

### Pipeline
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/onboard` | full onboarding in one LangGraph call |

---

## 📦 Installation

### Prerequisites
- Python 3.12+, PostgreSQL 16+, (optional) Redis

### Quick start

```bash
git clone https://github.com/ydvlalit03/My-Job-Searching-Partner.git
cd My-Job-Searching-Partner

cp .env.example .env            # fill in API keys (see below)

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

docker compose up -d db redis   # start Postgres (+ Redis)
python scripts/init_db.py        # create tables

uvicorn app.main:app --reload    # http://localhost:8000/docs
```

Full stack in one command: `docker compose up --build`.

---

## 🔐 Environment variables

```env
# LLM (pick one)
LLM_PROVIDER=gemini              # or "openai"
GEMINI_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
LLM_MODEL=gemini-2.0-flash       # or "gpt-4o-mini"

# Job Search
RAPIDAPI_KEY=your-rapidapi-key
RAPIDAPI_HOST=jsearch.p.rapidapi.com

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jobdhundo

# Auth
SECRET_KEY=your-random-secret-key
```

---

## 🗂️ Project structure

```
app/
├── api/v1/endpoints/   # auth, users, resume, career, jobs, roadmap, pipeline
├── core/               # config, security (JWT+bcrypt), deps
├── db/                 # async base + session
├── models/             # SQLAlchemy ORM models
├── schemas/            # Pydantic request/response
├── services/           # resume_parser, career_recommender, ats_scorer,
│                       #   job_search, roadmap_generator, pipeline, llm_client
└── main.py
alembic/                # migrations
scripts/init_db.py
docker-compose.yml · Dockerfile · requirements.txt
```

---

## 🧩 Design decisions

| Decision | Rationale |
|----------|-----------|
| **UUID primary keys** | no sequential ID leakage; multi-tenant / SaaS safe |
| **Async everything** | async SQLAlchemy + httpx = high concurrency for 100K+ users |
| **LLM-first with fallbacks** | every AI service degrades gracefully to rule-based logic |
| **LangGraph orchestration** | composable, retryable, observable multi-step workflows |
| **JSONB columns** | flexible schema evolution without migrations |
| **Connection pooling** | configurable pool (default 20 + 10 overflow) |
| **Modular services** | each module independently testable and replaceable |

---

## 🗺️ Roadmap

- [ ] Frontend (React / Next.js)
- [ ] Email verification + OAuth (Google) login
- [ ] AI resume builder
- [ ] Interview-prep module
- [ ] Redis rate limiting + Celery background jobs
- [ ] Multi-tenant SaaS mode + analytics dashboard
- [ ] Mobile app (React Native)

---

## 📄 License

MIT — built with AI by [ydvlalit03](https://github.com/ydvlalit03).
