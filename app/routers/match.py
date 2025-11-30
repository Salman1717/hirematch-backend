# backend/routers/match.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.semantic_matcher import match_resume_to_job


router = APIRouter()

class MatchRequest(BaseModel):
    resume_text: str
    job_text: str
    resume_skills: list = None
    job_required_skills: list = None
    semantic_weight: float = 0.6
    keyword_weight: float = 0.4

@router.post("/match")
def match(req: MatchRequest):
    result = match_resume_to_job(
        resume_text=req.resume_text,
        job_text=req.job_text,
        resume_skills=req.resume_skills or [],
        job_required_skills=req.job_required_skills or [],
        semantic_weight=req.semantic_weight,
        keyword_weight=req.keyword_weight
    )
    return result
