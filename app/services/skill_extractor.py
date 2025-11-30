import re
import spacy
import json
from typing import List, Dict, Any

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# ---------------------------------------------
# HARD SKILLS DICTIONARY (Tech-stack)
# ---------------------------------------------

HARD_SKILLS = {
    "Programming": [
        "python", "java", "javascript", "typescript", "c++", "swift",
        "dart", "kotlin", "go", "rust", "sql", "nosql"
    ],
    "Web/Mobile": [
        "react", "next.js", "angular", "vue", "flutter", "swiftui",
        "android", "ios", "node", "express"
    ],
    "Backend": [
        "django", "fastapi", "flask", "spring boot", "laravel", "graphql",
        "microservices"
    ],
    "ML/AI": [
        "machine learning", "deep learning", "nlp", "transformers","pytorch",
        "tensorflow", "scikit-learn", "huggingface"
    ],
    "Data Engineering": [
        "pyspark", "airflow", "kafka", "hadoop", "spark", "etl", "big data"
    ],
    "Cloud/DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "linux", "ci/cd", "jenkins", "github actions"
    ],
    "Databases": [
        "postgresql", "mysql", "mongodb", "redis", "dynamodb", "snowflake"
    ],
    "Testing": [
        "pytest", "selenium", "cypress", "postman", "unit testing", "integration testing"
    ]
}

# Flatten list for quick lookup
FLAT_HARD_SKILLS = set([skill.lower() for cat in HARD_SKILLS.values() for skill in cat])

# ---------------------------------------------
# SOFT SKILLS DICTIONARY
# ---------------------------------------------

SOFT_SKILLS = [
    "communication", "teamwork", "leadership", "problem solving",
    "critical thinking", "adaptability", "time management", "creativity",
    "attention to detail", "collaboration", "work ethic", "decision making",
    "self-motivated", "flexibility", "project management"
]

# ---------------------------------------------
# CLEAN TEXT
# ---------------------------------------------

def normalize(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()

# ---------------------------------------------
# EXTRACT SKILLS
# ---------------------------------------------

def extract_skills(text: str) -> Dict[str, Any]:
    """
    Extracts hard and soft skills from resume/job description
    using dictionary + NLP noun chunks.
    """

    clean_text = normalize(text)
    doc = nlp(clean_text)

    found_hard = set()
    found_soft = set()

    # 1. Keyword matching (fast & accurate)
    for skill in FLAT_HARD_SKILLS:
        if skill in clean_text:
            found_hard.add(skill)

    for skill in SOFT_SKILLS:
        if skill in clean_text:
            found_soft.add(skill)

    # 2. NLP-based extraction (noun chunks → detect skills)
    for chunk in doc.noun_chunks:
        c = chunk.text.lower().strip()

        # Detect hard skills from noun chunks
        if c in FLAT_HARD_SKILLS:
            found_hard.add(c)

        # Detect soft skills heuristically
        if c in SOFT_SKILLS:
            found_soft.add(c)

    # 3. Remove noise
    found_hard = sorted(list(found_hard))
    found_soft = sorted(list(found_soft))

    return {
        "hard_skills": found_hard,
        "soft_skills": found_soft
    }

# ---------------------------------------------
# SAVE Results → skills_extracted.json
# ---------------------------------------------

def save_skills_to_json(text: str, filename: str = "skills_extracted.json"):
    skills = extract_skills(text)
    with open(filename, "w") as f:
        json.dump(skills, f, indent=4)
    return skills


# CLI TEST
if __name__ == "__main__":
    sample = """
    Experienced iOS developer skilled in Swift, SwiftUI, Python, CI/CD,
    Docker, AWS, teamwork, communication, problem solving.
    """
    print(save_skills_to_json(sample))
