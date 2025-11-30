import json
from typing import List, Dict

# ----------------------------
# Load Dubai Skills Dictionary
# ----------------------------

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/
DATA_DIR = os.path.join(BASE_DIR, "data")
SKILL_FILE = os.path.join(DATA_DIR, "skills_dubai.json")

with open(SKILL_FILE, "r") as f:
    DUBAI_SKILLS = json.load(f)


# -----------------------------------
# Normalize helper
# -----------------------------------

def normalize(skill: str) -> str:
    return skill.strip().lower()

# -----------------------------------
# Flatten Dubai skill lists for detection
# -----------------------------------

def flatten_dubai_skills() -> Dict[str, List[str]]:
    hard = []
    soft = []
    tools = []
    cloud = []

    for domain, data in DUBAI_SKILLS.items():
        hard.extend(data.get("Skills", []))
        tools.extend(data.get("Tools", []))
        cloud.extend(data.get("Cloud", []))

    # Global soft skills list (hardcoded)
    soft = [
        "communication", "teamwork", "leadership", "problem solving",
        "critical thinking", "adaptability", "time management", "creativity",
        "attention to detail", "collaboration", "work ethic", "decision making",
        "self-motivated", "flexibility", "project management"
    ]

    return {
        "hard": [normalize(s) for s in hard],
        "soft": [normalize(s) for s in soft],
        "tools": [normalize(s) for s in tools],
        "cloud": [normalize(s) for s in cloud]
    }

FLAT = flatten_dubai_skills()

# -----------------------------------
# Missing skills detection
# -----------------------------------

def detect_missing_skills(
    resume_skills: List[str],
    job_required_skills: List[str]
) -> Dict[str, List[str]]:
    
    resume_set = set(normalize(s) for s in resume_skills)
    job_set = set(normalize(s) for s in job_required_skills)

    # basic differences
    missing = job_set - resume_set
    matched = job_set & resume_set

    missing_hard = []
    missing_soft = []
    missing_tools = []
    missing_cloud = []

    for skill in missing:
        if skill in FLAT["hard"]:
            missing_hard.append(skill)
        elif skill in FLAT["soft"]:
            missing_soft.append(skill)
        elif skill in FLAT["tools"]:
            missing_tools.append(skill)
        elif skill in FLAT["cloud"]:
            missing_cloud.append(skill)
        else:
            # default bucket → hard
            missing_hard.append(skill)

    # Improvement tips
    tips = []
    if missing_cloud:
        tips.append("Cloud skills like AWS or Azure are strongly preferred in Dubai.")
    if missing_tools:
        tips.append("Consider learning tools such as Docker or Kubernetes.")
    if missing_hard:
        tips.append("Strengthen your core technical stack for better match.")
    if missing_soft:
        tips.append("Dubai recruiters value soft skills such as communication.")

    return {
        "missing_hard_skills": sorted(list(set(missing_hard))),
        "missing_soft_skills": sorted(list(set(missing_soft))),
        "missing_tools": sorted(list(set(missing_tools))),
        "missing_cloud": sorted(list(set(missing_cloud))),
        "matched_skills": sorted(list(matched)),
        "improvement_tips": tips
    }

# -----------------------------------
# Quick test
# -----------------------------------

if __name__ == "__main__":
    resume = ["swift", "swiftui", "git", "docker"]
    job_req = ["swift", "swiftui", "aws", "git", "rest api"]

    out = detect_missing_skills(resume, job_req)
    print(json.dumps(out, indent=2))
