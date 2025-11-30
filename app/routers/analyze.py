from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
import tempfile
import os

from app.services.parser_resume import parse_resume
from app.services.resume_cleaner import build_clean_resume_json
from app.services.skill_extractor import extract_skills
from app.services.parser_job import parse_job_text
from app.services.semantic_matcher import match_resume_to_job
from app.services.missing_skills import detect_missing_skills


router = APIRouter()

# ---------------------------------------------------------
# /analyze Endpoint
# ---------------------------------------------------------

@router.post("/analyze")
async def analyze_resume_and_job(
    resume_file: UploadFile = File(...),
    job_description: str = Form(...)
):

    # -------------------------
    # 1) Save uploaded resume
    # -------------------------
    temp_path = None
    try:
        suffix = resume_file.filename.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            temp_path = tmp.name
            content = await resume_file.read()
            tmp.write(content)

        # -------------------------
        # 2) Parse raw resume text
        # -------------------------
        raw_resume_text = parse_resume(temp_path)

        # -------------------------
        # 3) Clean + extract structured resume
        # -------------------------
        cleaned_resume = build_clean_resume_json(raw_resume_text)
        resume_clean_text = cleaned_resume.get("clean_text", "")

        # Resume skills
        resume_skill_data = extract_skills(resume_clean_text)
        resume_hard = resume_skill_data.get("hard_skills", [])
        resume_soft = resume_skill_data.get("soft_skills", [])
        resume_all_skills = resume_hard + resume_soft

        # -------------------------
        # 4) Parse job description
        # -------------------------
        job_data = parse_job_text(job_description)
        job_clean_text = job_data.get("clean_text", "")

        # Job required skills
        job_req_skills = job_data.get("tools_and_tech", [])
        job_req_skills = [s.lower() for s in job_req_skills]

        # -------------------------
        # 5) Missing Skills
        # -------------------------
        missing_skill_data = detect_missing_skills(
            resume_skills=resume_all_skills,
            job_required_skills=job_req_skills
        )

        # -------------------------
        # 6) Semantic Match Score
        # -------------------------
        match_result = match_resume_to_job(
            resume_text=resume_clean_text,
            job_text=job_clean_text,
            resume_skills=resume_all_skills,
            job_required_skills=job_req_skills,
        )

        # -------------------------
        # 7) Final Response
        # -------------------------
        return {
            "status": "success",
            "resume": {
                "raw": raw_resume_text,
                "clean": resume_clean_text,
                "sections": cleaned_resume,
                "skills": resume_skill_data,
            },
            "job": {
                "clean": job_clean_text,
                "parsed": job_data,
                "required_skills": job_req_skills,
            },
            "matching": {
                "semantic": match_result["semantic_sim"],
                "keyword_ratio": match_result["keyword_ratio"],
                "final_score": match_result["final_score"],
                "top_matches": match_result["top_matches"],
            },
            "missing_skills": missing_skill_data
        }

    finally:
        # cleanup temp file
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
