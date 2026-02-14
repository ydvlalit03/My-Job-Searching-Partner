from fastapi import APIRouter

from app.api.v1.endpoints import auth, career, jobs, pipeline, resume, roadmap, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(resume.router)
api_router.include_router(career.router)
api_router.include_router(jobs.router)
api_router.include_router(roadmap.router)
api_router.include_router(pipeline.router)
