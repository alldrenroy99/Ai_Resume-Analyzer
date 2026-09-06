"""
app.py
------
AI Resume Analyzer — a modern, animated Streamlit web app.

Upload a PDF resume and instantly get:
    - Extracted candidate & contact information
    - Detected technical skills as badges
    - An ATS (Applicant Tracking System) compatibility score
    - Strengths, weaknesses, and personalized recommendations

All parsing / scoring logic lives in resume_utils.py — this file is
responsible only for layout, styling, and presentation.

Run with:
    streamlit run app.py
"""

import time
import streamlit as st

import resume_utils as ru


# =====================================================================
# PAGE CONFIG
# =====================================================================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =====================================================================
# CUSTOM CSS — animations, cards, badges, gradients, hover effects
# =====================================================================

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ---------- Animated gradient header ---------- */
.hero-container {
    background: linear-gradient(-45deg, #6366f1, #8b5cf6, #ec4899, #6366f1);
    background-size: 300% 300%;
    animation: gradientShift 10s ease infinite;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(99, 102, 241, 0.25);
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.hero-title {
    font-family: 'Poppins', sans-serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: white;
    margin: 0;
    animation: fadeInDown 0.8s ease;
}
.hero-subtitle {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.05rem;
    margin-top: 0.5rem;
    animation: fadeInUp 0.8s ease;
}
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-15px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(15px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Fade-in for content sections ---------- */
.fade-in {
    animation: fadeIn 0.6s ease-in;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ---------- Section card ---------- */
.section-card {
    background: var(--background-color, #ffffff);
    border: 1px solid rgba(120, 120, 150, 0.15);
    border-radius: 16px;
    padding: 1.5rem 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.section-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 28px rgba(99, 102, 241, 0.15);
}
.section-title {
    font-family: 'Poppins', sans-serif;
    font-size: 1.15rem;
    font-weight: 600;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ---------- Stat tile ---------- */
.stat-tile {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 14px;
    padding: 1.1rem 1rem;
    color: white;
    text-align: center;
    transition: transform 0.2s ease;
}
.stat-tile:hover { transform: scale(1.04); }
.stat-value {
    font-family: 'Poppins', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
}
.stat-label {
    font-size: 0.82rem;
    opacity: 0.9;
    margin-top: 0.15rem;
}

/* ---------- Contact info row ---------- */
.contact-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 0.9rem;
    border-radius: 10px;
    margin-bottom: 0.5rem;
    background: rgba(120, 120, 150, 0.06);
    transition: background 0.2s ease;
}
.contact-row:hover { background: rgba(99, 102, 241, 0.12); }
.contact-label { font-weight: 600; opacity: 0.85; }
.contact-value-found { color: #16a34a; font-weight: 500; }
.contact-value-missing { color: #dc2626; font-weight: 500; }

/* ---------- Skill badge ---------- */
.badge-container { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.4rem; }
.skill-badge {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    color: white;
    background: linear-gradient(135deg, #6366f1, #ec4899);
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    animation: popIn 0.4s ease;
}
.skill-badge:hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 0 6px 14px rgba(99, 102, 241, 0.45);
}
.skill-badge-missing {
    background: rgba(120, 120, 150, 0.12);
    color: #6b7280;
    border: 1px dashed rgba(120, 120, 150, 0.4);
    box-shadow: none;
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.8); }
    to   { opacity: 1; transform: scale(1); }
}

/* ---------- Category label ---------- */
.category-label {
    font-weight: 600;
    font-size: 0.9rem;
    margin-top: 0.7rem;
    margin-bottom: 0.2rem;
    opacity: 0.75;
}

/* ---------- Animated progress bar (ATS score) ---------- */
.progress-outer {
    width: 100%;
    background: rgba(120, 120, 150, 0.15);
    border-radius: 999px;
    height: 22px;
    overflow: hidden;
    margin: 0.4rem 0 0.2rem 0;
}
.progress-inner {
    height: 100%;
    border-radius: 999px;
    text-align: right;
    color: white;
    font-size: 0.75rem;
    font-weight: 700;
    line-height: 22px;
    padding-right: 10px;
    width: 0%;
    animation: growBar 1.2s ease-out forwards;
    box-shadow: 0 0 12px rgba(0,0,0,0.15) inset;
}
@keyframes growBar { to { width: var(--target-width); } }

/* ---------- Mini progress bar (breakdown rows) ---------- */
.mini-progress-outer {
    width: 100%;
    background: rgba(120, 120, 150, 0.15);
    border-radius: 999px;
    height: 10px;
    overflow: hidden;
    margin-top: 4px;
}
.mini-progress-inner {
    height: 100%;
    border-radius: 999px;
    width: 0%;
    animation: growBar 1s ease-out forwards;
}

/* ---------- Strength / weakness pills ---------- */
.pill-list-item {
    padding: 0.55rem 0.8rem;
    border-radius: 10px;
    margin-bottom: 0.45rem;
    font-size: 0.92rem;
    animation: fadeIn 0.5s ease;
}
.pill-strength { background: rgba(34, 197, 94, 0.12); border-left: 4px solid #22c55e; }
.pill-weakness { background: rgba(239, 68, 68, 0.10); border-left: 4px solid #ef4444; }
.pill-recommend { background: rgba(99, 102, 241, 0.10); border-left: 4px solid #6366f1; }

/* ---------- Upload zone helper text ---------- */
.upload-hint {
    text-align: center;
    opacity: 0.7;
    font-size: 0.9rem;
    margin-top: -0.4rem;
    margin-bottom: 1rem;
}

/* Hide Streamlit's default hamburger/footer clutter for a cleaner look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =====================================================================
# UI HELPER FUNCTIONS
# =====================================================================

def render_hero():
    """Render the animated gradient hero header."""
    st.markdown(
        """
        <div class="hero-container">
            <p class="hero-title">🧠 AI Resume Analyzer</p>
            <p class="hero-subtitle">
                Upload your resume and get instant, AI-assisted insights on
                contact details, skills, and ATS compatibility.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_tile(column, value, label):
    """Render a single gradient statistic tile inside a given column."""
    with column:
        st.markdown(
            f"""
            <div class="stat-tile">
                <div class="stat-value">{value}</div>
                <div class="stat-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_contact_row(label: str, value):
    """Render one row in the contact-details card, clearly flagging missing info."""
    if value:
        display_value = value if not str(value).startswith("http") else \
            f'<a href="{value}" target="_blank">{value}</a>'
        st.markdown(
            f"""
            <div class="contact-row">
                <span class="contact-label">{label}</span>
                <span class="contact-value-found">✅ {display_value}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="contact-row">
                <span class="contact-label">{label}</span>
                <span class="contact-value-missing">❌ Not Found</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_skill_badges(skills: list, missing: bool = False):
    """Render a list of skills as pill-shaped badges."""
    css_class = "skill-badge skill-badge-missing" if missing else "skill-badge"
    badges_html = "".join(f'<span class="{css_class}">{skill}</span>' for skill in skills)
    st.markdown(f'<div class="badge-container">{badges_html}</div>', unsafe_allow_html=True)


def render_ats_progress_bar(score: float):
    """Render the big animated ATS score progress bar with a color tied to score."""
    if score >= 75:
        color = "#22c55e"   # green
    elif score >= 50:
        color = "#f59e0b"   # amber
    else:
        color = "#ef4444"   # red

    st.markdown(
        f"""
        <div class="progress-outer">
            <div class="progress-inner" style="background:{color}; --target-width:{score}%;">
                {score}%
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_progress(label: str, value: float, max_value: float):
    """Render a small labeled progress bar for one ATS score component."""
    pct = (value / max_value) * 100 if max_value else 0
    st.markdown(
        f"""
        <div style="margin-bottom:0.6rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.85rem;">
                <span>{label}</span><span>{value}/{max_value}</span>
            </div>
            <div class="mini-progress-outer">
                <div class="mini-progress-inner" style="background:#6366f1; --target-width:{pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pill_list(items: list, style: str):
    """Render a list of strengths / weaknesses / recommendations as colored pills."""
    css_class = {"strength": "pill-strength", "weakness": "pill-weakness", "recommend": "pill-recommend"}[style]
    icon = {"strength": "💪", "weakness": "⚠️", "recommend": "💡"}[style]
    for item in items:
        st.markdown(
            f'<div class="pill-list-item {css_class}">{icon} {item}</div>',
            unsafe_allow_html=True,
        )


def section_header(icon: str, title: str):
    st.markdown(f'<div class="section-title">{icon} {title}</div>', unsafe_allow_html=True)


# =====================================================================
# SIDEBAR
# =====================================================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    target_role = st.selectbox(
        "Target job role (for skill-gap suggestions)",
        options=list(ru.ROLE_SKILL_MAP.keys()),
        index=0,
    )
    st.markdown("---")
    st.markdown(
        """
        **How it works**
        1. Upload your resume as a PDF
        2. We extract text with `pypdf`
        3. Contact info & skills are parsed automatically
        4. An ATS score and recommendations are generated

        _Nothing is stored — all analysis happens in this session._
        """
    )
    st.markdown("---")
    st.caption("Built with Python, Streamlit & PyPDF 🚀")


# =====================================================================
# MAIN PAGE
# =====================================================================

render_hero()

uploaded_file = st.file_uploader(
    "📄 Drag and drop your resume here, or click to browse",
    type=["pdf"],
    help="Only PDF files are supported.",
)
st.markdown(
    '<p class="upload-hint">Supported format: PDF &nbsp;|&nbsp; Max size: 200MB</p>',
    unsafe_allow_html=True,
)

if uploaded_file is not None:
    with st.spinner("🔍 Reading and analyzing your resume..."):
        time.sleep(0.4)  # brief pause so the spinner + animations feel intentional
        resume_text = ru.extract_text_from_pdf(uploaded_file)

    if not resume_text.strip():
        st.error(
            "⚠️ We couldn't extract any text from this PDF. It may be a "
            "scanned image rather than a text-based document."
        )
        st.stop()

    # ---- Run all analysis ----
    contact_info = ru.get_contact_info(resume_text)
    skills_by_category = ru.detect_skills(resume_text)
    found_skills = ru.flatten_skills(skills_by_category)
    ats_result = ru.calculate_ats_score(resume_text, contact_info, found_skills)
    analysis = ru.analyze_strengths_weaknesses(contact_info, found_skills, ats_result)
    missing_skills = ru.suggest_missing_skills(found_skills, target_role)
    recommendations = ru.generate_recommendations(contact_info, missing_skills, analysis["weaknesses"])
    stats = ru.get_resume_stats(contact_info, found_skills, ats_result)

    st.success("✅ Resume analyzed successfully!")

    # ---- Top statistics row ----
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    stat_cols = st.columns(4)
    render_stat_tile(stat_cols[0], stats["total_skills"], "Skills Found")
    render_stat_tile(stat_cols[1], f'{stats["contact_filled"]}/{stats["contact_total"]}', "Contact Fields")
    render_stat_tile(stat_cols[2], f'{stats["completeness_pct"]}%', "Resume Completeness")
    render_stat_tile(stat_cols[3], f'{stats["ats_score"]}%', "ATS Score")
    st.markdown("</div>", unsafe_allow_html=True)

    st.write("")  # spacer

    # ---- Candidate Info + Contact Details ----
    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
        section_header("🧑‍💼", "Candidate Information")
        name = contact_info.get("name")
        if name:
            st.markdown(f"#### {name}")
        else:
            st.markdown("#### ❌ Name Not Found")
        st.caption(f"Total word count: {stats['word_count']}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
        section_header("📇", "Contact Details")
        render_contact_row("Email", contact_info.get("email"))
        render_contact_row("Phone", contact_info.get("phone"))
        render_contact_row("LinkedIn", contact_info.get("linkedin"))
        render_contact_row("GitHub", contact_info.get("github"))
        render_contact_row("Portfolio", contact_info.get("portfolio"))
        st.markdown("</div>", unsafe_allow_html=True)

    # ---- Skills Section ----
    st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
    section_header("🛠️", f"Technical Skills ({len(found_skills)} found)")
    if skills_by_category:
        for category, skills in skills_by_category.items():
            st.markdown(f'<div class="category-label">{category}</div>', unsafe_allow_html=True)
            render_skill_badges(skills)
    else:
        st.warning("No predefined technical skills were detected in this resume.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- ATS Score Section ----
    st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
    section_header("📊", "ATS Compatibility Score")
    render_ats_progress_bar(ats_result["total"])
    st.write("")
    breakdown_cols = st.columns(2)
    breakdown_items = list(ats_result["breakdown"].items())
    max_values = {
        "Contact Completeness": 20,
        "Skills Coverage": 25,
        "Section Structure": 25,
        "Impact & Action Verbs": 15,
        "Resume Length": 15,
    }
    for idx, (label, value) in enumerate(breakdown_items):
        with breakdown_cols[idx % 2]:
            render_mini_progress(label, value, max_values.get(label, 100))
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Resume Analysis: Strengths & Weaknesses ----
    st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
    section_header("🔎", "Resume Analysis")
    strengths_col, weaknesses_col = st.columns(2)
    with strengths_col:
        st.markdown("**Strengths**")
        render_pill_list(analysis["strengths"], "strength")
    with weaknesses_col:
        st.markdown("**Weaknesses**")
        render_pill_list(analysis["weaknesses"], "weakness")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Skill Gap for Target Role ----
    st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
    section_header("🎯", f"Suggested Skills for {target_role}")
    if missing_skills:
        st.caption("Skills commonly expected for this role that weren't found in your resume:")
        render_skill_badges(missing_skills, missing=True)
    else:
        st.success("You already cover all the key skills for this role. 🎉")
    st.markdown("</div>", unsafe_allow_html=True)

    # ---- Recommendations ----
    st.markdown('<div class="section-card fade-in">', unsafe_allow_html=True)
    section_header("💡", "Improvement Recommendations")
    render_pill_list(recommendations, "recommend")
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.info("👆 Upload a PDF resume above to get started.")
