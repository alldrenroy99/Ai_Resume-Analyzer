# 🧠 AI Resume Analyzer

A modern, animated Streamlit web app that analyzes PDF resumes: extracting
contact info, detecting technical skills, scoring ATS compatibility, and
generating personalized improvement recommendations.

## Features

- 🎨 Modern animated UI — gradient hero header, hover-effect cards, animated progress bars
- 📤 Drag-and-drop PDF upload
- 🧑‍💼 Extracts Full Name, Email, Phone, LinkedIn, GitHub, and Portfolio (clearly marks anything **Not Found**)
- ✉️ Emails are shown exactly as written in the resume — no case changes or mangling
- 🛠️ Detects technical skills from a predefined list and displays them as badges, grouped by category
- 📊 ATS compatibility score (0–100) with a full breakdown by component
- 🔎 Strengths & weaknesses analysis
- 🎯 Missing-skill suggestions based on a selected target job role
- 💡 Actionable improvement recommendations
- 📈 Summary statistics: skills found, contact completeness, resume completeness, ATS score

## Project Structure

```
resume_analyzer/
├── app.py            # Streamlit UI (layout, styling, presentation only)
├── resume_utils.py   # All parsing / scoring / analysis logic (UI-free, testable)
├── requirements.txt  # Python dependencies
└── README.md
```

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

## How It Works

1. **Upload** a PDF resume via the drag-and-drop uploader.
2. **Text extraction** — `pypdf` pulls raw text from every page.
3. **Contact parsing** — regex-based extraction for name, email, phone,
   LinkedIn, GitHub, and portfolio URLs. Anything not found is clearly
   labeled "Not Found" instead of guessed.
4. **Skill detection** — the extracted text is checked against a
   predefined, categorized skill list (`SKILL_CATEGORIES` in
   `resume_utils.py`) using whole-word matching.
5. **ATS scoring** — a weighted score (contact completeness, skill
   coverage, section structure, quantifiable impact, resume length).
6. **Analysis & recommendations** — strengths/weaknesses are derived from
   the score breakdown, and a target-role selector suggests skills you
   might be missing.

## Customizing

- **Add/remove skills:** edit `SKILL_CATEGORIES` in `resume_utils.py`.
- **Add job roles for skill-gap suggestions:** edit `ROLE_SKILL_MAP`.
- **Adjust ATS scoring weights:** edit `calculate_ats_score()`.
- **Restyle the UI:** all CSS lives in the `CUSTOM_CSS` string at the top
  of `app.py`.

## Notes

- Scanned/image-only PDFs (no embedded text layer) can't be parsed by
  `pypdf`; the app will show a clear warning in that case.
- Nothing is uploaded to a server or stored — analysis happens entirely
  in-memory for the current session.
