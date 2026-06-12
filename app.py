#!/usr/bin/env python
"""Streamlit front-end for ResumeForge AI. Run with: streamlit run app.py"""
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
from resumeforge.models import JobDetails
from resumeforge.pipeline import run_pipeline
from resumeforge.utils.clean_job_description import clean_job_description

st.set_page_config(page_title="ResumeForge AI", page_icon="📄", layout="centered")
st.title("ResumeForge AI")
st.caption("Tailor your resume to a job description — analyzed, rewritten, and validated by AI.")

with st.form("job_form"):
    company_name = st.text_input("Company Name")
    job_title = st.text_input("Job Title")
    location = st.text_input("Location")
    job_id = st.text_input("Job ID (optional)")
    job_description = st.text_area("Job Description", height=300, placeholder="Paste the full job description here...")
    submitted = st.form_submit_button("Tailor Resume", type="primary")

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
        with st.status("Running pipeline...", expanded=True) as status:

            def on_stage(message: str) -> None:
                status.update(label=message)
                st.write(message)

            try:
                result = run_pipeline(job_details, on_stage=on_stage)
                status.update(label="✓ Done", state="complete", expanded=False)
                st.session_state["result"] = result
            except Exception as e:
                status.update(label="Pipeline failed", state="error")
                st.error(f"{e}")

if "result" in st.session_state:
    result = st.session_state["result"]
    report = result.validation_report
    keywords = report.keyword_analysis

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
        f"{keywords.keywords_integrated}/{keywords.total_keywords_from_job}",
        f"{keywords.integration_rate:.1f}%",
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
