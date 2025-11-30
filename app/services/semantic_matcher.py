# backend/services/semantic_matcher.py
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# lazy-load model on first import
_MODEL = None

def get_embedding_model(model_name: str = "sentence-transformers/all-mpnet-base-v2"):
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(model_name)
    return _MODEL

# -------------------------
# Helpers
# -------------------------
def embed_texts(texts: List[str], model=None) -> np.ndarray:
    """
    Returns a 2D numpy array (n_texts x dim).
    """
    if model is None:
        model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings

def mean_pool(embs: np.ndarray) -> np.ndarray:
    """
    Average pooling across rows to get a single vector.
    """
    if embs is None or len(embs) == 0:
        return np.zeros((1, 768)).flatten()
    return np.mean(embs, axis=0)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """
    Single cosine similarity between 1-D vectors a and b.
    Returns value in [0,1].
    """
    if a is None or b is None:
        return 0.0
    a = a.reshape(1, -1)
    b = b.reshape(1, -1)
    sim = cosine_similarity(a, b)[0][0]
    # numerical safety
    sim = float(np.clip(sim, -1.0, 1.0))
    # map [-1,1] -> [0,1] (optional). We'll keep natural cosine in [-1,1] and scale later.
    # Here we transform to [0,1]:
    return (sim + 1.0) / 2.0

# -------------------------
# Keyword match ratio
# -------------------------
def keyword_match_ratio(required_keywords: List[str], resume_keywords: List[str]) -> float:
    """
    Fraction of required_keywords that appear (exact or fuzzy lowercased) in resume_keywords.
    Returns value in [0,1].
    """
    if not required_keywords:
        return 0.0
    # lower-case sets
    req = [r.lower().strip() for r in required_keywords if r and r.strip()]
    res = [s.lower().strip() for s in resume_keywords if s and s.strip()]
    if not req:
        return 0.0
    matched = 0
    res_set = set(res)
    for r in req:
        # exact match or substring match
        if r in res_set:
            matched += 1
        else:
            # allow partial matches: any resume token contains r or r contains resume token
            for s in res:
                if r in s or s in r:
                    matched += 1
                    break
    ratio = matched / len(req)
    return float(max(0.0, min(1.0, ratio)))

# -------------------------
# Main matching function
# -------------------------
def match_resume_to_job(
    resume_text: str,
    job_text: str,
    resume_skills: List[str] = None,
    job_required_skills: List[str] = None,
    model_name: str = "sentence-transformers/all-mpnet-base-v2",
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4
) -> Dict[str, Any]:
    """
    Returns a detailed match report:
    {
      "semantic_sim": 0.85,
      "keyword_ratio": 0.6,
      "final_score": 82.0,
      "details": { ... }
    }
    - resume_skills and job_required_skills are lists of normalized skill strings (optional).
    - final_score is in [0,100].
    """
    model = get_embedding_model(model_name)

    # 1) split into logical chunks for embeddings
    # For resume: we embed lines / sentences to capture experience bullets
    resume_sentences = [s for s in resume_text.split("\n") if s.strip()] or [resume_text]
    job_sentences = [s for s in job_text.split("\n") if s.strip()] or [job_text]

    # embed
    resume_embs = embed_texts(resume_sentences, model=model)
    job_embs = embed_texts(job_sentences, model=model)

    # pool
    resume_vec = mean_pool(resume_embs)
    job_vec = mean_pool(job_embs)

    # semantic similarity in [0,1]
    semantic_sim = cosine_sim(resume_vec, job_vec)

    # 2) keyword ratio
    kw_ratio = 0.0
    if job_required_skills and resume_skills:
        kw_ratio = keyword_match_ratio(job_required_skills, resume_skills)
    elif job_required_skills:
        # fallback: count job_required_skills substrings in resume_text
        hits = 0
        for req in job_required_skills:
            if req.lower() in resume_text.lower():
                hits += 1
        kw_ratio = hits / len(job_required_skills) if job_required_skills else 0.0
    else:
        kw_ratio = 0.0

    # 3) combine scores
    semantic_w = float(semantic_weight)
    keyword_w = float(keyword_weight)
    combined = semantic_w * semantic_sim + keyword_w * kw_ratio
    final_score_0_100 = float(round(combined * 100.0, 2))

    # 4) also compute top-N sentence pair similarities (for explainability)
    # compute pairwise similarity matrix and get top matches
    try:
        pair_sims = cosine_similarity(resume_embs, job_embs)
        # find top matches (resume_idx, job_idx, score)
        matches = []
        r_count, j_count = pair_sims.shape
        for i in range(r_count):
            for j in range(j_count):
                matches.append((i, j, float(pair_sims[i, j])))
        matches_sorted = sorted(matches, key=lambda x: x[2], reverse=True)[:6]
        top_matches = [
            {
                "resume_snippet": resume_sentences[i] if i < len(resume_sentences) else "",
                "job_snippet": job_sentences[j] if j < len(job_sentences) else "",
                "cosine": float(round((m + 1.0)/2.0, 4))  # converted to [0,1]
            }
            for i, j, m in matches_sorted
        ]
    except Exception:
        top_matches = []

    return {
        "semantic_sim": round(semantic_sim, 4),
        "keyword_ratio": round(kw_ratio, 4),
        "final_score": final_score_0_100,
        "weights": {"semantic": semantic_w, "keyword": keyword_w},
        "top_matches": top_matches,
        "meta": {
            "resume_sentences": len(resume_sentences),
            "job_sentences": len(job_sentences)
        }
    }
