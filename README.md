# Job Dhundo

**AI-powered job search platform for freshers** — find the best matching jobs, optimize your resume for ATS, and get a structured daily application roadmap.

Built with FastAPI, PostgreSQL, Google Gemini / OpenAI, and LangGraph.

---

## Features

### 1. Smart Resume Parsing
- Upload your resume (PDF) and get structured extraction of skills, experience, and education
- LLM-powered parsing with regex fallback for reliability
- Merges LLM + regex results for maximum skill coverage

### 2. Career Recommendation Engine
- Get top 5 job role suggestions based on your profile
- LLM reasoning considers market demand, skill transferability, and career growth
- Falls back to keyword-based Jaccard similarity matching

### 3. Job Matching Engine
- Searches fresher-friendly jobs via RapidAPI (JSearch)
- Ranks jobs by skill match, location fit, and experience level
- Returns top 20 jobs with detailed match scores

### 4. ATS Resume Scoring (0-100)
- LLM evaluates your resume like a real recruiter
- Scores across 4 dimensions: keywords, action verbs, achievements, formatting
- Returns missing keywords and actionable improvement suggestions

### 5. Daily Roadmap Generator
- LLM-personalized daily action plan for your job search
- Tracks applications, referrals, and recruiter connections
- Auto-completes days when all targets are hit

### 6. Referral Message Generator
- LLM-generated cold outreach messages for LinkedIn
- Personalized based on target role, company, and your background

### 7. One-Call Onboarding Pipeline (LangGraph)
- Upload resume → Parse → Recommend roles → Search jobs → ATS score
- All in a single API call powered by LangGraph StateGraph
- Conditional routing with graceful error handling at each node

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL + SQLAlchemy (async) |
| AI/LLM | Google Gemini SDK / OpenAI SDK |
| Orchestration | LangGraph (multi-step AI workflows) |
| Job Search | RapidAPI (JSearch) |
| PDF Parsing | pdfplumber |
| Auth | JWT (PyJWT + bcrypt) |
| Migrations | Alembic |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
job-dhundo/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py              # Register, login (JWT)
│   │   │   ├── users.py             # Profile, onboarding
│   │   │   ├── resume.py            # Upload, parse, ATS score
│   │   │   ├── career.py            # Role recommendations
│   │   │   ├── jobs.py              # Search, rank, save, track
│   │   │   ├── roadmap.py           # Daily plan, progress, referral msgs
│   │   │   └── pipeline.py          # LangGraph one-call onboarding
│   │   └── router.py
│   ├── core/
│   │   ├── config.py                # Pydantic settings (env-based)
│   │   ├── security.py              # JWT + bcrypt
│   │   └── deps.py                  # Auth dependency
│   ├── db/
│   │   ├── base.py                  # DeclarativeBase
│   │   └── session.py               # Async session factory
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic request/response schemas
│   ├── services/
│   │   ├── llm_client.py            # Gemini/OpenAI unified client
│   │   ├── resume_parser.py         # LLM + regex PDF parser
│   │   ├── career_recommender.py    # LLM + keyword role matching
│   │   ├── ats_scorer.py            # LLM + rule-based ATS scoring
│   │   ├── job_search.py            # RapidAPI integration + ranking
│   │   ├── roadmap_generator.py     # LLM + template daily plans
│   │   └── pipeline.py              # LangGraph StateGraph pipeline
│   ├── utils/
│   ├── workers/                     # Future: background tasks
│   └── main.py                      # FastAPI app entry point
├── alembic/                         # Database migrations
├── tests/
├── scripts/init_db.py               # Dev table creation
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Database Schema

```
┌──────────────┐     ┌───────────────────┐     ┌────────────────────────┐
│    users      │────│  resume_profiles   │     │ career_recommendations │
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
        │
        ├─────────────────────┐
        │                     │
┌───────────────┐     ┌────────────────┐
│  saved_jobs    │     │ roadmap_entries │
├───────────────┤     ├────────────────┤
│ id (UUID)      │     │ id (UUID)       │
│ user_id (FK)   │     │ user_id (FK)    │
│ title          │     │ date            │
│ company        │     │ jobs_to_apply   │
│ match_score    │     │ referrals_to_send│
│ match_details  │     │ jobs_applied    │
│ status         │     │ daily_tips      │
│ apply_url      │     │ is_completed    │
└───────────────┘     └────────────────┘
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT token |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/users/me` | Get current user profile |
| PATCH | `/api/v1/users/me/onboard` | Set preferences (location, remote, salary) |

### Resume
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resume/upload` | Upload and parse resume (PDF) |
| GET | `/api/v1/resume/profile` | Get parsed resume data |
| POST | `/api/v1/resume/ats-score` | Get ATS score (0-100) with suggestions |

### Career
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/career/recommend` | Get top 5 role recommendations |
| POST | `/api/v1/career/select-roles` | Select target roles |

### Jobs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/jobs/search` | Search and rank jobs |
| POST | `/api/v1/jobs/save/{index}` | Save a matched job |
| GET | `/api/v1/jobs/saved` | List saved jobs |
| PATCH | `/api/v1/jobs/saved/{id}/status` | Update application status |

### Roadmap
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/roadmap/generate` | Generate weekly action plan |
| GET | `/api/v1/roadmap/today` | Get today's tasks |
| PATCH | `/api/v1/roadmap/{id}/progress` | Update daily progress |
| POST | `/api/v1/roadmap/referral-message` | Generate referral message |

### Pipeline (LangGraph)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/pipeline/onboard` | Full onboarding in one call |

---

## LangGraph Pipeline

```
                        ┌─────────────────┐
                        │  parse_resume    │
                        │  (LLM + regex)   │
                        └────────┬────────┘
                                 │
                          [has skills?]
                           /         \
                         yes          no
                         /              \
            ┌───────────────────┐      END
            │ recommend_careers  │
            │   (LLM + keyword)  │
            └────────┬──────────┘
                     │
              [has recommendations?]
                /            \
              yes              no
              /                 \
┌──────────────────┐    ┌──────────────┐
│   search_jobs     │    │  ats_score    │
│ (RapidAPI + rank) │    │ (LLM + rules) │
└────────┬─────────┘    └──────┬───────┘
         │                      │
         └──────┐       ┌──────┘
                │       │
         ┌──────────────┐
         │  ats_score    │
         │ (LLM + rules) │
         └──────┬───────┘
                │
               END
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Redis (optional, for caching at scale)

### Quick Start

```bash
# Clone the repo
git clone https://github.com/ydvlalit03/My-Job-Searching-Partner.git
cd My-Job-Searching-Partner

# Set up environment
cp .env.example .env
# Edit .env and fill in your API keys:
#   - GEMINI_API_KEY (from Google AI Studio)
#   - RAPIDAPI_KEY (from RapidAPI - JSearch)
#   - SECRET_KEY (generate a random string)

# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL (via Docker)
docker compose up -d db redis

# Create database tables
python scripts/init_db.py

# Run the server
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

### Docker (Full Stack)

```bash
cp .env.example .env
# Fill in API keys in .env

docker compose up --build
```

This starts PostgreSQL, Redis, and the API server together.

---

## Environment Variables

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

## Architecture Decisions

| Decision | Rationale |
|---|---|
| **UUID primary keys** | No sequential ID leakage, multi-tenant safe for SaaS |
| **Async everything** | SQLAlchemy async + httpx async = high concurrency for 100K+ users |
| **LLM-first with fallbacks** | Every AI service degrades gracefully to rule-based logic |
| **LangGraph orchestration** | Composable, retryable, observable multi-step AI workflows |
| **JSONB columns** | Flexible schema evolution without migrations |
| **Connection pooling** | Configurable pool size (default 20 + 10 overflow) |
| **Modular services** | Each module independently testable and replaceable |
| **Docker Compose** | One command to spin up the full stack |

---

## Roadmap

- [ ] Frontend (React / Next.js)
- [ ] Email verification flow
- [ ] OAuth login (Google)
- [ ] Resume builder with AI suggestions
- [ ] Interview prep module
- [ ] Rate limiting with Redis
- [ ] Background job processing (Celery)
- [ ] Multi-tenant SaaS mode
- [ ] Analytics dashboard
- [ ] Mobile app (React Native)

---

## License

MIT

---

Built with AI by [ydvlalit03](https://github.com/ydvlalit03)
