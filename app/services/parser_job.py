import re
import json
from typing import Dict, List, Any
import spacy
from yake import KeywordExtractor

nlp = spacy.load("en_core_web_sm")

# small curated tech + IT terms to help identify Tools/Tech
DEFAULT_TECH_LIST = [
    "python","java","javascript","react","node","django","flask","swift","kotlin","flutter",
    "aws","azure","gcp","docker","kubernetes","sql","postgresql","mongodb","pytorch","tensorflow",
    "nlp","spark","hadoop","git","ci/cd","rest api","graphql","microservices","linux"
]

def normalize_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_sections_from_job(text: str) -> Dict[str, str]:
    """
    Heuristic splitting of job description into Responsibilities / Requirements / Others
    Look for headings like 'Responsibilities', 'Requirements', 'Skills', 'What you'll do'
    """
    lines = text.splitlines()
    headings = []
    for idx, ln in enumerate(lines):
        ln_low = ln.lower().strip()
        if any(h in ln_low for h in ["responsibil", "requirement", "qualification", "skill", "what you'll", "what you will", "you will", "you are"]):
            headings.append((idx, ln.strip()))

    if not headings:
        # fallback: try to split by blank lines into paragraphs
        paras = [p.strip() for p in text.split("\n\n") if p.strip()]
        return {"description": " ".join(paras)}

    sections = {}
    for i, (pos, hdr) in enumerate(headings):
        start = pos + 1
        end = headings[i+1][0] if i+1 < len(headings) else len(lines)
        content = " ".join(lines[start:end]).strip()
        sections[hdr] = content
    return sections


def extract_tech_tools(text: str, top_k: int = 30) -> List[str]:
    """
    Combine YAKE keyword extraction with a tech keyword filter to get tools/tech list.
    """
    kw_extractor = KeywordExtractor(top=top_k, features=None)
    keywords = kw_extractor.extract_keywords(text)
    # keywords is list of (kw, score)
    extracted = [kw for kw, _ in keywords]
    final = []
    text_lower = text.lower()
    # keep keywords that match our DEFAULT_TECH_LIST or appear capitalized / common tech patterns
    for kw in extracted:
        if any(tok in kw.lower() for tok in DEFAULT_TECH_LIST):
            final.append(kw)
        elif re.search(r"[A-Z]{2,}", kw):  # acronyms like AWS, SQL
            final.append(kw)
        elif " " not in kw and len(kw) <= 20 and kw.lower() in text_lower:
            # short single token likely tech token
            final.append(kw)
        if len(final) >= top_k:
            break

    # ensure we also include direct matches of DEFAULT_TECH_LIST
    for t in DEFAULT_TECH_LIST:
        if t in text_lower and t not in final:
            final.append(t)
    # dedupe preserving order
    seen = set()
    out = []
    for itm in final:
        if itm not in seen:
            seen.add(itm)
            out.append(itm)
    return out[:top_k]


def extract_requirements_and_responsibilities(text: str) -> Dict[str, str]:
    sections = extract_sections_from_job(text)
    # naive assignment
    responsibilities = []
    requirements = []
    other = []

    for hdr, content in sections.items():
        hdr_low = hdr.lower()
        if "respons" in hdr_low or "what you'll" in hdr_low or "you will" in hdr_low:
            responsibilities.append(content)
        elif "require" in hdr_low or "qualif" in hdr_low or "skill" in hdr_low:
            requirements.append(content)
        else:
            other.append(content)

    # fallback: if nothing found, try to heuristically split by sentences
    if not responsibilities and not requirements:
        doc = nlp(text)
        for sent in doc.sents:
            s = sent.text.strip()
            if any(w in s.lower() for w in ["responsible", "responsibilities", "work with", "collaborate", "lead", "design", "develop"]):
                responsibilities.append(s)
            elif any(w in s.lower() for w in ["require", "requirement", "must have", "qualification", "experience", "years"]):
                requirements.append(s)
            else:
                other.append(s)

    return {
        "responsibilities": " ".join(responsibilities).strip(),
        "requirements": " ".join(requirements).strip(),
        "other": " ".join(other).strip()
    }


def parse_job_text(raw_text: str) -> Dict[str, Any]:
    text = normalize_text(raw_text)
    sections = extract_sections_from_job(text)
    rr = extract_requirements_and_responsibilities(text)
    tools = extract_tech_tools(text)
    # also collect noun chunks as potential phrases
    doc = nlp(text)
    noun_chunks = [nc.text.strip() for nc in doc.noun_chunks][:60]
    return {
        "raw_text": raw_text,
        "clean_text": text,
        "sections": sections,
        "responsibilities": rr.get("responsibilities"),
        "requirements": rr.get("requirements"),
        "tools_and_tech": tools,
        "noun_chunks": noun_chunks
    }


# CLI quick test
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("Provide text file path with job description.")
        exit(1)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    print(json.dumps(parse_job_text(raw), indent=2)[:4000])
