"""Deterministic keyword matching for project scoring and resume coverage.

LLM-free helpers reused by the Streamlit app to (1) rank projects against a job
description and (2) show which job keywords made it into the tailored resume.
"""
from resumeforge.models import JobAnalysis, MasterProject, Resume


def job_keywords(job_analysis: JobAnalysis) -> list[str]:
    """Flatten the categorized skills into a de-duped keyword list.

    Responsibilities/qualifications are long phrases, so they are left to the
    LLM validator rather than matched here.
    """
    skills = job_analysis.skills
    all_terms = skills.technical + skills.soft + skills.management + skills.bonus
    seen: dict[str, str] = {}
    for term in all_terms:
        term = term.strip()
        if term and term.lower() not in seen:
            seen[term.lower()] = term
    return list(seen.values())


def match_keywords(keywords: list[str], text: str) -> tuple[list[str], list[str]]:
    """Split keywords into (matched, missing) by case-insensitive substring.

    Substring (not word-boundary) matching keeps terms like "C++", ".NET" and
    "CI/CD" working.
    """
    haystack = text.lower()
    matched, missing = [], []
    for kw in keywords:
        if kw.lower() in haystack:
            matched.append(kw)
        else:
            missing.append(kw)
    return matched, missing


def score_project(project: MasterProject, keywords: list[str]) -> tuple[int, list[str]]:
    """Return (match count, matched keywords) for a project against the keywords."""
    text = f"{project.tech_stack or ''} {project.description}"
    matched, _ = match_keywords(keywords, text)
    return len(matched), matched


def resume_text(resume: Resume) -> str:
    """Concatenate the searchable content of a tailored resume."""
    content = resume.resume_content
    parts: list[str] = []
    for exp in content.work_experience:
        parts.extend(exp.responsibilities)
    for project in content.projects:
        parts.extend(project.description)
        if project.tech_stack:
            parts.append(project.tech_stack)
    for skill in content.skills:
        parts.extend(skill.items)
    return "\n".join(parts)
