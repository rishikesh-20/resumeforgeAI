#!/usr/bin/env python
"""Streamlit front-end for ResumeForge AI. Run with: streamlit run app.py"""
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from resumeforge.models import JobDetails, MasterProject
from resumeforge.pipeline import analyze_job_description, tailor_resume
from resumeforge.utils.clean_job_description import clean_job_description
from resumeforge.utils.keyword_match import (
    job_keywords,
    match_keywords,
    resume_text,
    score_project,
)
from resumeforge.utils.read_projects import read_projects, save_project

st.set_page_config(page_title="ResumeForge AI", page_icon="📄", layout="centered")
st.title("ResumeForge AI")
st.caption("Tailor your resume to a job description — analyzed, rewritten, and validated by AI.")

# ── Step 1: Job details ──────────────────────────────────────────────────────
with st.form("job_form"):
    company_name = st.text_input("Company Name")
    job_title = st.text_input("Job Title")
    location = st.text_input("Location")
    job_id = st.text_input("Job ID (optional)")
    job_description = st.text_area("Job Description", height=300, placeholder="Paste the full job description here...")
    submitted = st.form_submit_button("Analyze Job", type="primary")

if submitted:
    missing = [
        label
        for label, value in [
            ("Company Name", company_name),
            ("Job Title", job_title),
            ("Location", location),
            ("Job Description", job_description),
        ]
        if not value.strip()
    ]
    if missing:
        st.error(f"Please fill in: {', '.join(missing)}")
    else:
        job_details = JobDetails(
            company_name=company_name.strip(),
            job_title=job_title.strip(),
            location=location.strip(),
            job_id=job_id.strip() or None,
            job_description=clean_job_description(job_description.strip()),
            date_applied=datetime.now().strftime("%m-%d-%Y"),
        )
        st.session_state.pop("result", None)
        with st.status("Analyzing job description...", expanded=False) as status:
            try:
                st.session_state["job_analysis"] = analyze_job_description(job_details.job_description)
                st.session_state["job_details"] = job_details
                status.update(label="✓ Job analyzed", state="complete")
            except Exception as e:
                status.update(label="Analysis failed", state="error")
                st.error(f"{e}")

# ── Step 2: Projects ─────────────────────────────────────────────────────────
if "job_analysis" in st.session_state:
    job_analysis = st.session_state["job_analysis"]
    job_details = st.session_state["job_details"]
    keywords = job_keywords(job_analysis)

    st.header("Projects")
    st.caption("Projects are ranked by how many job keywords they match. Pick which to include.")

    with st.expander("➕ Add a project"):
        with st.form("add_project_form", clear_on_submit=True):
            p_name = st.text_input("Project name")
            p_tech = st.text_input("Tech stack (comma-separated)")
            p_date = st.text_input("Date (e.g. December 2025)")
            p_desc = st.text_area("Description", height=150, placeholder="Full project description — the AI rewrites this into bullets.")
            add = st.form_submit_button("Add Project")
        if add:
            if not p_name.strip() or not p_desc.strip():
                st.error("Project name and description are required.")
            else:
                project = MasterProject(
                    name=p_name.strip(),
                    tech_stack=p_tech.strip() or None,
                    date=p_date.strip() or None,
                    description=p_desc.strip(),
                )
                path = save_project(project)
                st.success(f"Saved to {path.relative_to(Path.cwd())}")
                st.rerun()

    projects = read_projects()
    scored = sorted(
        ((p, *score_project(p, keywords)) for p in projects),
        key=lambda t: t[1],
        reverse=True,
    )

    selected = []
    for rank, (project, count, matched) in enumerate(scored):
        col_check, col_info = st.columns([1, 9])
        checked = col_check.checkbox(
            "include", value=rank < 3, key=f"proj_{project.name}", label_visibility="collapsed"
        )
        col_info.markdown(f"**{project.name}** — {count} keyword match{'es' if count != 1 else ''}")
        if matched:
            col_info.caption("Matched: " + ", ".join(matched))
        if checked:
            selected.append(project)

    if st.button("Tailor Resume", type="primary", disabled=not selected):
        st.session_state.pop("result", None)
        with st.status("Running pipeline...", expanded=True) as status:

            def on_stage(message: str) -> None:
                status.update(label=message)
                st.write(message)

            try:
                result = tailor_resume(job_details, job_analysis, selected, on_stage=on_stage)
                status.update(label="✓ Done", state="complete", expanded=False)
                st.session_state["result"] = result
            except Exception as e:
                status.update(label="Pipeline failed", state="error")
                st.error(f"{e}")

# ── Step 3: Results ──────────────────────────────────────────────────────────
if "result" in st.session_state:
    result = st.session_state["result"]
    report = result.validation_report
    kw = report.keyword_analysis

    st.header("Validation Report")
    if report.passed_validation:
        st.success("Validation passed")
    else:
        st.warning("Validation did not pass — review the feedback below before submitting.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall", f"{report.overall_score}/100")
    col2.metric("ATS", f"{report.feedback.ats_score}/100")
    col3.metric("Readability", f"{report.feedback.human_readability_score}/100")
    col4.metric(
        "Keywords",
        f"{kw.keywords_integrated}/{kw.total_keywords_from_job}",
        f"{kw.integration_rate:.1f}%",
    )

    if report.feedback.strengths:
        with st.expander("Strengths"):
            for s in report.feedback.strengths:
                st.markdown(f"✓ {s}")
    if report.feedback.weaknesses:
        with st.expander("Weaknesses"):
            for w in report.feedback.weaknesses:
                st.markdown(f"✗ {w}")
    if report.feedback.suggestions:
        with st.expander("Suggestions"):
            for s in report.feedback.suggestions:
                st.markdown(f"→ {s}")

    st.header("Keyword Coverage")
    keywords = job_keywords(st.session_state["job_analysis"])
    included, missing = match_keywords(keywords, resume_text(result.resume))
    st.caption(f"{len(included)}/{len(keywords)} job keywords appear in the resume (literal scan).")
    inc_col, miss_col = st.columns(2)
    with inc_col:
        st.markdown("**Included**")
        for k in included:
            st.markdown(f"<span style='color:green'>✓ {k}</span>", unsafe_allow_html=True)
    with miss_col:
        st.markdown("**Missing**")
        for k in missing:
            st.markdown(f"<span style='color:#c0392b'>✗ {k}</span>", unsafe_allow_html=True)

    with st.expander("Validator's keyword judgment (AI)"):
        if kw.naturally_integrated_keywords:
            st.markdown("**Naturally integrated:** " + ", ".join(kw.naturally_integrated_keywords))
        if kw.missing_critical_keywords:
            st.markdown("**Missing critical:** " + ", ".join(kw.missing_critical_keywords))
        if report.phrase_analysis.missing_important_phrases:
            st.markdown("**Missing important phrases:** " + ", ".join(report.phrase_analysis.missing_important_phrases))

    st.header("Resume")
    tex_path = Path(result.tex_path)
    tex_source = tex_path.read_text(encoding="utf-8")
    st.download_button(
        "Download .tex",
        data=tex_source,
        file_name=tex_path.name,
        mime="application/x-tex",
        type="primary",
    )
    st.caption(f"Saved to {result.tex_path} and logged to Notion. Compile with pdflatex or Overleaf.")
    with st.expander("LaTeX source", expanded=True):
        st.code(tex_source, language="latex")
