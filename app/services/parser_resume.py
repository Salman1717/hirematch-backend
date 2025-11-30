import re
from pdfminer.high_level import extract_text
from docx import Document

# -------------------------------
# Clean extracted text
# -------------------------------

def clean_resume_text(text: str) -> str:
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove non-ascii junk (common in copy/paste resumes)
    text = text.encode("ascii", "ignore").decode()

    return text.strip()


# -------------------------------
# Extract text from PDF
# -------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        text = extract_text(pdf_path)
        return clean_resume_text(text)
    except Exception as e:
        print("PDF parsing error:", e)
        return ""


# -------------------------------
# Extract text from DOCX
# -------------------------------

def extract_text_from_docx(docx_path: str) -> str:
    try:
        doc = Document(docx_path)
        full_text = []

        for para in doc.paragraphs:
            full_text.append(para.text)

        text = "\n".join(full_text)
        return clean_resume_text(text)

    except Exception as e:
        print("DOCX parsing error:", e)
        return ""


# -------------------------------
# Wrapper — auto detect file type
# -------------------------------

def parse_resume(file_path: str) -> str:
    """
    Auto-detect the file extension and parse the resume accordingly.
    """
    file_path = file_path.lower()

    if file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)

    elif file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)

    else:
        raise ValueError("Unsupported file format: only PDF or DOCX allowed.")
