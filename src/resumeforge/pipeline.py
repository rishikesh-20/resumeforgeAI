"""Shared pipeline orchestration used by both the CLI and the Streamlit app."""
from typing import Callable, List, NamedTuple, Optional

from resumeforge.agents import run_job_analyst, run_resume_tailor, run_resume_validator
from resumeforge.exceptions import DataLoadError
from resumeforge.models import JobAnalysis, JobDetails, MasterProject, Resume, ResumeValidationReport
from resumeforge.utils.read_json import read_resume_json
from resumeforge.utils.read_projects import read_projects
from resumeforge.utils.resume_latex_generator import generate_latex_resume
from resumeforge.utils.notion_tracker import track_application


class PipelineResult(NamedTuple):
    resume: Resume
    validation_report: ResumeValidationReport
    tex_path: str


def analyze_job_description(job_description: str) -> JobAnalysis:
    """Phase 1: extract structured keywords/requirements from the job description."""
    return run_job_analyst(job_description)


def tailor_resume(
    job_details: JobDetails,
    job_analysis: JobAnalysis,
    projects: List[MasterProject],
    on_stage: Optional[Callable[[str], None]] = None,
) -> PipelineResult:
    """Phase 2: tailor against the given projects, validate, generate LaTeX, track."""

    def notify(message: str) -> None:
        if on_stage:
            on_stage(message)

    if not projects:
        raise DataLoadError(
            "No projects selected. Add or select at least one project before tailoring."
        )

    master_resume = read_resume_json()
    resume_content_dict = {
        "work_experience": [exp.model_dump() for exp in master_resume.work_experience],
        "education": [edu.model_dump() for edu in master_resume.education],
        "skills": [skill.model_dump() for skill in master_resume.skills],
    }

    notify("[1/2] Tailoring resume (local model — may take a few minutes)...")
    resume_content = run_resume_tailor(resume_content_dict, projects, job_analysis)

    for i, exp in enumerate(resume_content.work_experience):
        if not exp.location and i < len(master_resume.work_experience):
            exp.location = master_resume.work_experience[i].location
    for i, edu in enumerate(resume_content.education):
        if not edu.location and i < len(master_resume.education):
            edu.location = master_resume.education[i].location

    notify("[2/2] Validating resume...")
    validation_report = run_resume_validator(job_analysis, resume_content)

    header = master_resume.header.model_copy()
    header.location = job_details.location
    final_resume = Resume(header=header, resume_content=resume_content)

    notify("Generating LaTeX...")
    tex_path = generate_latex_resume(final_resume, job_details)

    track_application(job_details)

    return PipelineResult(final_resume, validation_report, tex_path)


def run_pipeline(
    job_details: JobDetails,
    on_stage: Optional[Callable[[str], None]] = None,
) -> PipelineResult:
    """Run the full tailoring pipeline: analyze, tailor, validate, generate LaTeX, track."""

    def notify(message: str) -> None:
        if on_stage:
            on_stage(message)

    all_projects = read_projects()
    if not all_projects:
        raise DataLoadError(
            "No projects found in data/projects/. Copy the example to get started:\n"
            "    cp data/projects/project.json.example data/projects/my-project.json\n"
            "Then fill in your project details and run again."
        )

    notify("Analyzing job description...")
    job_analysis = analyze_job_description(job_details.job_description)

    return tailor_resume(job_details, job_analysis, all_projects, on_stage=on_stage)
