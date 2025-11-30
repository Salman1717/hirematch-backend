# 📌 HireMatch — AI Resume–Job Match Engine (Dubai-Optimized)

HireMatch is an **NLP-powered Resume → Job Description matcher**, purpose-built for optimizing **Dubai hiring requirements** and improving **ATS compatibility**. It analyzes resumes, extracts skills, cleans job descriptions, performs semantic similarity, detects missing skills, and returns an ATS-friendly compatibility score.

Built with **FastAPI + spaCy + SentenceTransformers + Torch**, and deployed on **Render**.

---

## 🔗 Live Deployment & Documentation

| Component | URL |
| :--- | :--- |
| **Live API (Base URL)** | 👉 https://hirematch-analyzer.onrender.com |
| **Swagger Docs (API Reference)** | 👉 https://hirematch-analyzer.onrender.com/docs |

---

## 🚀 Key Features

### 🧠 Semantic Matching Engine
The core of HireMatch, powered by `sentence-transformers / all-mpnet-base-v2`, calculates the compatibility score:

* **Semantic Score:** Calculates **Cosine Similarity** between the resume and job description embeddings.
* **Keyword Score:** Measures **keyword overlap** for specific term matching.
* **Weighted Final Score:**
    $$Final\ Score = 0.6 \times Semantic\ Score + 0.4 \times Keyword\ Score$$

### 🔍 Resume Parsing
Utilizes `spaCy` and other parsers for robust extraction and cleaning:
* PDF & DOCX support
* Header/footer removal & Contact extraction
* Section splitting (skills, experience, education, projects, summary)
* **Skill Extraction** (with noun chunks + heuristics)

### 📝 Job Description Parsing
Efficiently extracts key requirements using techniques like YAKE keyword extraction:
* Requirements & Responsibilities extraction
* Keyword mining
* Tech stack detection

### 💡 Missing Skills Detector
Provides actionable feedback to candidates, crucial for optimizing resumes:
* Lists **Missing Hard Skills**
* Lists **Missing Soft Skills**
* Lists **Missing Cloud/DevOps Tools**
* Personalized improvement tips

---

## ⚡ REST API Endpoints

| Endpoint | Description |
| :--- | :--- |
| `/api/analyze` | Full end-to-end analysis: resume parsing, job parsing, matching score, and missing skills detection. |
| `/api/match` | Pure semantic and keyword score calculation only. |

* *Full API documentation is available via **Swagger Docs**.*

---

## 💻 Tech Stack

| Category | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **Python 3.10, FastAPI** | High-performance, async framework for the API. |
| **NLP Core** | **spaCy 3.5, Transformers, Torch** | Used for efficient tokenization, entity recognition, and core NLP tasks. |
| **Semantic Matching** | **Sentence-Transformers** | Powers the embedding generation (`all-mpnet-base-v2`). |
| **Parsing** | **PDFMiner, Docx parser** | Handles file reading for PDF and DOCX formats. |
| **Keyword Extraction** | **YAKE** | Used for automated, high-quality keyword mining. |
| **Deployment** | **Render** | Cloud hosting service for the live backend. |

---

## 🗂 Project Structure

```bash
hirematch-backend/
│
├── app/
│ ├── main.py
│ ├── routers/
│ │ ├── analyze.py
│ │ └── init.py
│ ├── services/
│ │ ├── parser_resume.py
│ │ ├── parser_job.py
│ │ ├── resume_cleaner.py
│ │ ├── semantic_matcher.py
│ │ ├── missing_skills.py
│ │ └── init.py
│ └── init.py
│
├── requirements.txt
├── skills_dubai.json
├── README.md
```
---

## 🛠 Running Locally

Follow these steps to get the project running on your machine:

**1️⃣ Clone the Repository**
```bash
git clone https://github.com/Salman1717/hirematch-backend
cd hirematch-backend
```

**2️⃣ Install Dependencies**

Install the required Python packages and download the spaCy language model.
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm --direct
```

**3️⃣ Start the Server**

Run the FastAPI application using uvicorn.
Use --reload for automatic restarts during development.
```bash
uvicorn app.main:app --reload
```


Once running, visit the local API documentation at:
```bash
👉 http://127.0.0.1:8000/docs
```
---

## 👨‍💻 Author

**Salman Mhaskar**

🔗 LinkedIn: https://linkedin.com/in/salmanmhaskar-2a5660211

⭐ Support

If you find this project useful, please consider giving the repository a star! 🌟
Your support keeps the project growing.
