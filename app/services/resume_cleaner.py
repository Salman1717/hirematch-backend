import re
import json
from typing import Dict, List, Any
import spacy
from collections import defaultdict

nlp = spacy.load("en_core_web_sm")

EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_RE = re.compile(r"(\+?\d{1,3}[\s-])?(?:\(?\d{2,4}\)?[\s-]?)?\d{3,4}[\s-]?\d{3,4}")

SECTION_HEADERS = [
    "summary", "professional summary", "experience", "work experience", "employment history",
    "education", "skills", "technical skills", "projects", "certifications", "achievements",
    "publications", "interests", "contact", "objective"
]

def remove_headers_footers(text: str) -> str:
    """
    Heuristic removal of header/footer blocks: 
    Remove repeated short lines at top/bottom and lines containing multiple separators.
    """
    if not text:
        return ""

    lines = [ln.strip() for ln in text.splitlines() if ln.strip() != ""]
    if len(lines) == 0:
        return ""

    # Remove top block if it's mostly contact info or very short (header)
    top_block = lines[:6]
    header_lines = []
    for ln in top_block:
        if EMAIL_RE.search(ln) or PHONE_RE.search(ln) or len(ln.split()) <= 5:
            header_lines.append(ln)
    # If >=2 header-like lines at top, drop them
    if len(header_lines) >= 2:
        lines = lines[len(header_lines):]

    # Remove bottom footer block if similar pattern
    bottom_block = lines[-6:]
    footer_lines = []
    for ln in bottom_block:
        if ("page" in ln.lower() and any(ch.isdigit() for ch in ln)) or len(ln.split()) <= 4:
            footer_lines.append(ln)
    if len(footer_lines) >= 2:
        lines = lines[:-len(footer_lines)]

    return "\n".join(lines)


def normalize_formatting(text: str) -> str:
    # Remove HTML tags if any, emojis
    text = re.sub(r"<[^>]+>", " ", text)
    emoji_pattern = re.compile(
        "[" 
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub("", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize_sentences(text: str) -> List[str]:
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


def extract_contact_info(text: str) -> Dict[str, Any]:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    # phones regex returns groups; normalize to strings
    phones_clean = []
    for p in PHONE_RE.findall(text):
        # p may be tuple if groups; flatten
        if isinstance(p, tuple):
            phones_clean.append("".join([part for part in p if part]))
        else:
            phones_clean.append(p)
    phones_clean = phones_clean if phones_clean else PHONE_RE.findall(text)
    return {
        "emails": list(set(emails)),
        "phones": list(set([p for p in phones_clean if p]))
    }


def split_sections_by_headers(text: str) -> Dict[str, str]:
    """
    Split resume into sections using common headers.
    Returns dict header -> content (raw).
    """
    lines = text.splitlines()
    header_positions = []
    for idx, ln in enumerate(lines):
        ln_low = ln.lower().strip()
        for h in SECTION_HEADERS:
            # exact or startswith
            if ln_low.startswith(h):
                header_positions.append((idx, h))
                break

    sections = defaultdict(list)
    if not header_positions:
        # fallback: return whole text as 'content'
        sections["content"] = [text]
        return {k: "\n".join(v).strip() for k, v in sections.items()}

    # For each header, collect lines until next header
    for i, (pos, header) in enumerate(header_positions):
        start = pos + 1
        end = header_positions[i + 1][0] if i + 1 < len(header_positions) else len(lines)
        content_lines = lines[start:end]
        sections[header].extend(content_lines)

    return {k: "\n".join(v).strip() for k, v in sections.items()}


def extract_skills_from_text(text: str, max_skills=60) -> List[str]:
    """
    Heuristic skills extractor using noun chunks + simple token matching.
    """
    doc = nlp(text)
    candidates = set()

    # noun chunks
    for chunk in doc.noun_chunks:
        chunk_text = chunk.text.strip()
        # filter long/generic chunks
        if 1 < len(chunk_text) <= 60:
            candidates.add(chunk_text)

    # also collect capitalized tech-like tokens and known tech keywords
    tech_keywords = [
        "python","java","javascript","react","node","django","flask","swift","kotlin",
        "flutter","aws","azure","gcp","docker","kubernetes","sql","postgresql","mongodb",
        "pytorch","tensorflow","nlp","spark","hadoop","git","ci/cd","rest api","graphql"
    ]
    for kw in tech_keywords:
        if kw in text.lower():
            candidates.add(kw)

    # lightweight cleanup: drop ultra-generic tokens
    filtered = [c for c in candidates if len(c) > 2 and not c.lower() in ("experience", "years", "team", "work")]
    # return top N by appearance order (preserve original order as much as possible)
    ordered = []
    for token in filtered:
        if token not in ordered:
            ordered.append(token)
        if len(ordered) >= max_skills:
            break
    return ordered


def build_clean_resume_json(raw_text: str) -> Dict[str, Any]:
    """
    Full pipeline: remove header/footer, normalize, split sections, extract tokens.
    Returns structured JSON.
    """
    if not raw_text:
        return {}

    step1 = remove_headers_footers(raw_text)
    step2 = normalize_formatting(step1)
    contact = extract_contact_info(step2)
    sections = split_sections_by_headers(step1)  # use original line breaks for headers detection
    # combine skills from sections (if present)
    skills_text = sections.get("skills", "") or sections.get("technical skills", "") or ""
    skills_candidates = extract_skills_from_text(skills_text + " " + step2)

    # Experience: if explicit section not found, try heuristics
    experience_text = sections.get("experience") or sections.get("work experience") or ""
    if not experience_text:
        # try to capture paragraphs with 'years' or 'experience' keywords
        sentences = tokenize_sentences(step2)
        exp_sents = [s for s in sentences if any(k in s.lower() for k in ("experience", "years", "worked", "responsible", "led", "developed"))]
        experience_text = " ".join(exp_sents[:8])

    # Education
    education_text = sections.get("education", "") or ""
    # Projects
    projects_text = sections.get("projects", "") or ""
    # Summary
    summary_text = sections.get("summary") or sections.get("professional summary") or ""
    if not summary_text:
        # take first 2 sentences as summary
        sents = tokenize_sentences(step2)
        summary_text = " ".join(sents[:2])

    return {
        "raw_text": raw_text,
        "clean_text": step2,
        "contact": contact,
        "summary": summary_text.strip(),
        "skills": skills_candidates,
        "experience": experience_text.strip(),
        "education": education_text.strip(),
        "projects": projects_text.strip(),
        "sections_raw": sections
    }


# Quick CLI test helper
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Provide a file path with resume text (or run parse_resume to get raw).")
        sys.exit(1)

    # if path is a text file
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    out = build_clean_resume_json(raw)
    print(json.dumps(out, indent=2)[:4000])
