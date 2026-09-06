"""
resume_utils.py
----------------
Helper functions for the AI Resume Analyzer.

This module is intentionally kept UI-free: every function here takes plain
data in and returns plain data out (strings, lists, dicts). That makes the
logic easy to test and keeps app.py focused purely on presentation.

Sections in this file:
    1. PDF text extraction
    2. Contact info extraction (name, email, phone, linkedin, github, portfolio)
    3. Skill detection
    4. ATS score calculation
    5. Strengths / weaknesses / recommendations
    6. Resume statistics
"""

import re
from io import BytesIO
from pypdf import PdfReader


# =====================================================================
# 1. PDF TEXT EXTRACTION
# =====================================================================

def extract_text_from_pdf(uploaded_file) -> str:
    """
    Extract raw text from an uploaded PDF file using pypdf.

    Args:
        uploaded_file: A file-like object from st.file_uploader.

    Returns:
        The full extracted text as a single string. Returns an empty
        string if extraction fails or the PDF has no readable text.
    """
    try:
        # Read the uploaded file into memory so pypdf can parse it
        pdf_bytes = BytesIO(uploaded_file.read())
        reader = PdfReader(pdf_bytes)

        pages_text = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            pages_text.append(page_text)

        return "\n".join(pages_text)
    except Exception:
        # A corrupted or unreadable PDF should not crash the app
        return ""


# =====================================================================
# 2. CONTACT INFO EXTRACTION
# =====================================================================

# Words that should never be mistaken for a person's name
_NAME_BLOCKLIST = {
    "resume", "curriculum", "vitae", "cv", "profile", "summary",
    "objective", "contact", "email", "phone", "address", "linkedin",
    "github", "portfolio", "skills", "education", "experience",
}


def extract_email(text: str) -> str | None:
    """
    Extract the first valid email address EXACTLY as written in the resume.

    The regex is deliberately conservative so it does not "fix" or mangle
    real addresses (e.g. it will not lowercase them or strip characters
    that are legally part of an email's local part).
    """
    email_pattern = re.compile(
        r"[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"
    )
    match = email_pattern.search(text)
    if not match:
        return None

    # Return the exact matched substring -- no case changes, no trimming
    # beyond stray trailing punctuation that sometimes gets pulled in
    # from PDF line breaks (e.g. a trailing period or comma).
    raw_email = match.group(0)
    return raw_email.rstrip(".,;:")


def extract_phone(text: str) -> str | None:
    """
    Extract the first plausible phone number.

    Supports common formats: +country codes, dashes, dots, spaces,
    parentheses. Requires at least 9 digits total to avoid matching
    unrelated numbers (dates, zip codes, etc.).
    """
    phone_pattern = re.compile(
        r"(\+?\d{1,3}[\s.-]?)?"          # optional country code
        r"(\(?\d{2,4}\)?[\s.-]?)"        # area code
        r"\d{3,4}[\s.-]?\d{3,4}"         # main number
    )
    for match in phone_pattern.finditer(text):
        candidate = match.group(0).strip()
        digit_count = len(re.sub(r"\D", "", candidate))
        if 9 <= digit_count <= 14:
            return candidate
    return None


def extract_linkedin(text: str) -> str | None:
    """Extract a LinkedIn profile URL if present."""
    pattern = re.compile(
        r"(https?://)?(www\.)?linkedin\.com/[A-Za-z0-9\-_/%]+", re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        return _normalize_url(match.group(0))
    return None


def extract_github(text: str) -> str | None:
    """Extract a GitHub profile URL if present."""
    pattern = re.compile(
        r"(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+", re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        return _normalize_url(match.group(0))
    return None


def extract_portfolio(text: str, linkedin: str | None, github: str | None) -> str | None:
    """
    Extract a personal portfolio / website URL, if any.

    Strategy: find anything that looks like a web address (with or
    without an explicit http/www prefix, e.g. "janedoe.dev"), then
    discard ones that belong to LinkedIn, GitHub, or common non-portfolio
    domains (email providers, social platforms), leaving personal sites.
    """
    # Matches full URLs (http://..., www...) OR bare domains like
    # "johnsmithdev.com" / "janedoe.dev" that commonly appear next to a
    # "Portfolio:" label without a scheme or "www."
    url_pattern = re.compile(
        r"(https?://[^\s,)]+"
        r"|www\.[^\s,)]+\.[a-z]{2,}[^\s,)]*"
        r"|\b[A-Za-z0-9-]+\.(?:com|dev|io|me|net|org|xyz|app|site|tech)\b(?:/[^\s,)]*)?)",
        re.IGNORECASE,
    )
    excluded_domains = [
        "linkedin.com", "github.com", "gmail.com", "yahoo.com",
        "outlook.com", "hotmail.com", "twitter.com", "x.com",
        "facebook.com", "instagram.com",
    ]

    for match in url_pattern.finditer(text):
        candidate = match.group(0)
        # Skip if it's actually part of an email address
        start = match.start()
        if start > 0 and text[start - 1] == "@":
            continue
        if not any(domain in candidate.lower() for domain in excluded_domains):
            return _normalize_url(candidate.rstrip(".,;:"))

    return None


def extract_name(text: str) -> str | None:
    """
    Best-effort extraction of the candidate's full name.

    Heuristic: the name is almost always one of the first few non-empty
    lines of a resume, written in Title Case, containing 2-4 words, with
    no digits, email symbols, or section-header keywords.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines[:10]:  # only scan the top of the document
        words = line.split()
        if not (2 <= len(words) <= 4):
            continue
        if any(char.isdigit() for char in line):
            continue
        if "@" in line or "http" in line.lower():
            continue
        if any(word.lower().strip(",.") in _NAME_BLOCKLIST for word in words):
            continue
        # Most words should start with a capital letter (Title Case name)
        capitalized = sum(1 for w in words if w[0].isupper())
        if capitalized >= len(words) - 1:
            return line

    return None


def _normalize_url(url: str) -> str:
    """Ensure a URL has a scheme so it can be rendered as a clickable link."""
    if not url.startswith(("http://", "https://")):
        return f"https://{url}"
    return url


def get_contact_info(text: str) -> dict:
    """Bundle all contact-detail extraction into a single dictionary."""
    linkedin = extract_linkedin(text)
    github = extract_github(text)
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": linkedin,
        "github": github,
        "portfolio": extract_portfolio(text, linkedin, github),
    }


# =====================================================================
# 3. SKILL DETECTION
# =====================================================================

# Predefined skill list, grouped by category for nicer display
SKILL_CATEGORIES = {
    "Programming Languages": [
        "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "C",
        "Go", "Rust", "Kotlin", "Swift", "PHP", "Ruby", "R", "Scala",
        "MATLAB", "Perl", "Dart",
    ],
    "Web Development": [
        "HTML", "CSS", "React", "Angular", "Vue", "Next.js", "Node.js",
        "Express", "Django", "Flask", "FastAPI", "Spring Boot",
        "ASP.NET", "jQuery", "Bootstrap", "Tailwind CSS", "GraphQL",
        "REST API", "Streamlit",
    ],
    "Data Science & ML": [
        "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
        "Keras", "Scikit-learn", "Pandas", "NumPy", "OpenCV", "NLTK",
        "SpaCy", "Data Analysis", "Data Visualization", "Matplotlib",
        "Seaborn", "Power BI", "Tableau", "Statistics",
    ],
    "Databases": [
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "SQLite", "Redis",
        "Oracle", "Firebase", "Cassandra", "DynamoDB",
    ],
    "Cloud & DevOps": [
        "AWS", "Azure", "Google Cloud", "GCP", "Docker", "Kubernetes",
        "Jenkins", "CI/CD", "Terraform", "Ansible", "Linux", "Nginx",
        "GitHub Actions", "DevOps",
    ],
    "Tools & Platforms": [
        "Git", "GitHub", "GitLab", "Jira", "Postman", "VS Code",
        "IntelliJ", "Figma", "Excel", "PowerPoint",
    ],
    "Mobile Development": [
        "Android", "iOS", "Flutter", "React Native", "SwiftUI",
        "Kotlin Multiplatform",
    ],
}

# Flattened lookup used for role-based skill-gap suggestions
ROLE_SKILL_MAP = {
    "Software Engineer": [
        "Python", "Java", "C++", "Git", "SQL", "REST API", "Docker",
        "Data Structures", "Algorithms",
    ],
    "Frontend Developer": [
        "HTML", "CSS", "JavaScript", "React", "TypeScript",
        "Tailwind CSS", "Next.js", "Git",
    ],
    "Backend Developer": [
        "Python", "Node.js", "Django", "Flask", "SQL", "MongoDB",
        "REST API", "Docker", "AWS",
    ],
    "Full Stack Developer": [
        "JavaScript", "React", "Node.js", "SQL", "MongoDB", "Git",
        "REST API", "Docker", "HTML", "CSS",
    ],
    "Data Scientist": [
        "Python", "Pandas", "NumPy", "Machine Learning", "Scikit-learn",
        "TensorFlow", "SQL", "Data Visualization", "Statistics",
    ],
    "DevOps Engineer": [
        "Docker", "Kubernetes", "AWS", "Terraform", "Jenkins", "CI/CD",
        "Linux", "Ansible", "Git",
    ],
    "Mobile Developer": [
        "Kotlin", "Swift", "Flutter", "React Native", "Android", "iOS",
        "Git",
    ],
}


def detect_skills(text: str, skill_categories: dict = SKILL_CATEGORIES) -> dict:
    """
    Detect which predefined skills appear in the resume text.

    Uses whole-word, case-insensitive matching so short skill names
    (e.g. "R", "Go", "C") don't accidentally match inside other words.

    Returns:
        A dict mapping category name -> list of skills found in that
        category. Categories with no matches are omitted.
    """
    found_by_category = {}
    text_lower = text.lower()

    for category, skills in skill_categories.items():
        found = []
        for skill in skills:
            # Escape special regex characters (e.g. "C++", "C#")
            pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
            if re.search(pattern, text_lower):
                found.append(skill)
        if found:
            found_by_category[category] = found

    return found_by_category


def flatten_skills(skills_by_category: dict) -> list:
    """Flatten the category->skills dict into a single sorted list."""
    all_skills = []
    for skills in skills_by_category.values():
        all_skills.extend(skills)
    return sorted(set(all_skills))


def suggest_missing_skills(found_skills: list, target_role: str) -> list:
    """
    Compare the candidate's found skills against a target role's expected
    skill set and return what's missing.
    """
    required = ROLE_SKILL_MAP.get(target_role, [])
    found_lower = {s.lower() for s in found_skills}
    return [skill for skill in required if skill.lower() not in found_lower]


# =====================================================================
# 4. ATS SCORE CALCULATION
# =====================================================================

# Section headers commonly expected by Applicant Tracking Systems
_EXPECTED_SECTIONS = [
    "experience", "education", "skills", "summary", "objective",
    "projects", "certification", "achievements",
]

_ACTION_VERBS = [
    "led", "built", "developed", "designed", "managed", "created",
    "implemented", "improved", "launched", "optimized", "increased",
    "reduced", "achieved", "delivered", "engineered", "automated",
]


def calculate_ats_score(text: str, contact_info: dict, found_skills: list) -> dict:
    """
    Calculate an approximate ATS (Applicant Tracking System) compatibility
    score out of 100, broken into weighted components.

    Components (weights):
        - Contact completeness   : 20 pts
        - Skills present         : 25 pts
        - Key sections present   : 25 pts
        - Quantifiable results   : 15 pts
        - Resume length          : 15 pts
    """
    text_lower = text.lower()
    breakdown = {}

    # --- Contact completeness (20 pts) ---
    contact_fields = ["name", "email", "phone", "linkedin"]
    filled = sum(1 for field in contact_fields if contact_info.get(field))
    breakdown["Contact Completeness"] = round((filled / len(contact_fields)) * 20, 1)

    # --- Skills present (25 pts) ---
    skill_score = min(len(found_skills) / 10, 1.0) * 25  # 10+ skills = full marks
    breakdown["Skills Coverage"] = round(skill_score, 1)

    # --- Key sections present (25 pts) ---
    sections_found = sum(1 for section in _EXPECTED_SECTIONS if section in text_lower)
    section_score = min(sections_found / len(_EXPECTED_SECTIONS), 1.0) * 25
    breakdown["Section Structure"] = round(section_score, 1)

    # --- Quantifiable achievements / action verbs (15 pts) ---
    number_mentions = len(re.findall(r"\b\d+%?\b", text))
    verb_mentions = sum(1 for verb in _ACTION_VERBS if verb in text_lower)
    impact_score = min((number_mentions + verb_mentions) / 15, 1.0) * 15
    breakdown["Impact & Action Verbs"] = round(impact_score, 1)

    # --- Resume length (15 pts) --- ideal range ~300-900 words
    word_count = len(text.split())
    if 300 <= word_count <= 900:
        length_score = 15
    elif word_count < 300:
        length_score = max((word_count / 300) * 15, 0)
    else:
        length_score = max(15 - ((word_count - 900) / 100), 5)
    breakdown["Resume Length"] = round(length_score, 1)

    total_score = round(sum(breakdown.values()), 1)
    total_score = max(0, min(total_score, 100))

    return {
        "total": total_score,
        "breakdown": breakdown,
        "word_count": word_count,
    }


# =====================================================================
# 5. STRENGTHS, WEAKNESSES & RECOMMENDATIONS
# =====================================================================

def analyze_strengths_weaknesses(contact_info: dict, found_skills: list, ats_result: dict) -> dict:
    """
    Generate human-readable strengths and weaknesses based on the
    extracted data and ATS breakdown.
    """
    strengths = []
    weaknesses = []
    breakdown = ats_result["breakdown"]

    # Contact info
    if contact_info.get("email") and contact_info.get("phone"):
        strengths.append("Complete primary contact information (email & phone) is present.")
    else:
        weaknesses.append("Missing email or phone number — recruiters may not be able to reach you.")

    if contact_info.get("linkedin"):
        strengths.append("LinkedIn profile is included, boosting professional credibility.")
    else:
        weaknesses.append("No LinkedIn profile found — adding one strengthens your professional presence.")

    if contact_info.get("github"):
        strengths.append("GitHub profile is included, which is valuable for technical roles.")

    # Skills
    if len(found_skills) >= 10:
        strengths.append(f"Strong technical skill set detected ({len(found_skills)} skills found).")
    elif len(found_skills) >= 5:
        strengths.append(f"Solid technical foundation detected ({len(found_skills)} skills found).")
    else:
        weaknesses.append("Very few recognizable technical skills found — consider listing more relevant tools and technologies.")

    # Sections
    if breakdown.get("Section Structure", 0) >= 20:
        strengths.append("Resume includes most standard sections expected by ATS software.")
    else:
        weaknesses.append("Some standard resume sections (e.g. Summary, Projects, Certifications) may be missing.")

    # Impact
    if breakdown.get("Impact & Action Verbs", 0) >= 10:
        strengths.append("Good use of action verbs and quantifiable achievements.")
    else:
        weaknesses.append("Limited use of measurable results — try adding numbers (%, $, counts) to your accomplishments.")

    # Length
    word_count = ats_result["word_count"]
    if word_count < 200:
        weaknesses.append("Resume seems too short — add more detail about your experience and projects.")
    elif word_count > 1100:
        weaknesses.append("Resume seems long — consider trimming to keep it concise and focused.")
    else:
        strengths.append("Resume length is within an appropriate range.")

    return {"strengths": strengths, "weaknesses": weaknesses}


def generate_recommendations(contact_info: dict, missing_skills: list, weaknesses: list) -> list:
    """
    Turn weaknesses and missing skills into concrete, actionable
    improvement suggestions.
    """
    recommendations = []

    if not contact_info.get("linkedin"):
        recommendations.append("Add a LinkedIn profile URL near your contact details.")
    if not contact_info.get("github"):
        recommendations.append("Include a GitHub link to showcase your projects and code quality.")
    if not contact_info.get("portfolio"):
        recommendations.append("Consider adding a personal portfolio website to stand out.")

    if missing_skills:
        skill_list = ", ".join(missing_skills[:6])
        recommendations.append(f"For your target role, consider gaining or highlighting: {skill_list}.")

    for weakness in weaknesses:
        if "action verbs" in weakness.lower() or "measurable" in weakness.lower():
            recommendations.append("Start bullet points with strong action verbs (e.g. 'Led', 'Built', 'Optimized') and quantify results wherever possible.")
        if "sections" in weakness.lower():
            recommendations.append("Add clearly labeled sections such as Summary, Experience, Education, Skills, and Projects.")
        if "too short" in weakness.lower():
            recommendations.append("Expand on your work experience and projects with specific responsibilities and outcomes.")
        if "too long" in weakness.lower() or "long" in weakness.lower() and "consider trimming" in weakness.lower():
            recommendations.append("Trim less relevant details and keep the resume to 1-2 pages.")

    if not recommendations:
        recommendations.append("Great job! Your resume covers the essentials — keep it updated as you gain new skills.")

    # Remove duplicates while preserving order
    seen = set()
    unique_recs = []
    for rec in recommendations:
        if rec not in seen:
            seen.add(rec)
            unique_recs.append(rec)

    return unique_recs


# =====================================================================
# 6. RESUME STATISTICS
# =====================================================================

def get_resume_stats(contact_info: dict, found_skills: list, ats_result: dict) -> dict:
    """Compile top-level statistics for the dashboard-style summary cards."""
    contact_fields = ["name", "email", "phone", "linkedin", "github", "portfolio"]
    filled_fields = sum(1 for field in contact_fields if contact_info.get(field))
    completeness_pct = round((filled_fields / len(contact_fields)) * 100)

    return {
        "total_skills": len(found_skills),
        "contact_filled": filled_fields,
        "contact_total": len(contact_fields),
        "completeness_pct": completeness_pct,
        "ats_score": ats_result["total"],
        "word_count": ats_result["word_count"],
    }
