#!/usr/bin/env python
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from resumeforge.agents import run_job_analyst, run_resume_tailor, run_resume_validator
from resumeforge.utils.read_json import read_resume_json
from resumeforge.utils.read_projects import read_projects
from resumeforge.models import Resume, JobDetails
from resumeforge.utils.resume_latex_generator import generate_latex_resume
from resumeforge.utils.notion_tracker import track_application
from resumeforge.utils.clean_job_description import clean_job_description


def get_job_details_from_cli() -> JobDetails:
    print("=" * 80)
    print("RESUMEFORGE AI")
    print("=" * 80)

    company_name = input("Company Name: ").strip()
    job_title = input("Job Title: ").strip()
    location = input("Location: ").strip()
    job_id = input("Job ID (optional, press Enter to skip): ").strip()

    print("\nJob Description (paste below, then type 'END' on a new line and press Enter):")
    description_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        description_lines.append(line)

    job_details = JobDetails(
        company_name=company_name,
        job_title=job_title,
        location=location,
        job_id=job_id if job_id else None,
        job_description=clean_job_description("\n".join(description_lines).strip()),
        date_applied=datetime.now().strftime("%m-%d-%Y"),
    )

    print(f"\n✓ {company_name} — {job_title} ({job_details.date_applied})")
    return job_details


def run() -> None:
    try:
        job_details = get_job_details_from_cli()
        master_resume = read_resume_json()
        all_projects = read_projects()
        if not all_projects:
            print("⚠ No projects found in data/projects/. Copy the example to get started:")
            print("    cp data/projects/project.json.example data/projects/my-project.json")
            print("  Then fill in your project details and run again.")
            sys.exit(1)

        resume_content_dict = {
            "work_experience": [exp.model_dump() for exp in master_resume.work_experience],
            "education": [edu.model_dump() for edu in master_resume.education],
            "skills": [skill.model_dump() for skill in master_resume.skills],
        }

        print("\n[1/3] Analyzing job description...")
        job_analysis = run_job_analyst(job_details.job_description)

        print("[2/3] Tailoring resume (local model — may take a few minutes)...")
        resume_content = run_resume_tailor(resume_content_dict, all_projects, job_analysis)

        for i, exp in enumerate(resume_content.work_experience):
            if not exp.location and i < len(master_resume.work_experience):
                exp.location = master_resume.work_experience[i].location
        for i, edu in enumerate(resume_content.education):
            if not edu.location and i < len(master_resume.education):
                edu.location = master_resume.education[i].location

        print("[3/3] Validating resume...")
        validation_report = run_resume_validator(job_analysis, resume_content)

        print("\n" + "=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        print(f"Passed:        {validation_report.passed_validation}")
        print(f"Overall Score: {validation_report.overall_score}/100")
        print(f"ATS Score:     {validation_report.feedback.ats_score}/100")
        print(f"Readability:   {validation_report.feedback.human_readability_score}/100")
        print(f"Keywords:      {validation_report.keyword_analysis.keywords_integrated}/{validation_report.keyword_analysis.total_keywords_from_job} ({validation_report.keyword_analysis.integration_rate:.1f}%)")

        if validation_report.feedback.strengths:
            print("\nStrengths:")
            for s in validation_report.feedback.strengths:
                print(f"  ✓ {s}")
        if validation_report.feedback.weaknesses:
            print("\nWeaknesses:")
            for w in validation_report.feedback.weaknesses:
                print(f"  ✗ {w}")
        if validation_report.feedback.suggestions:
            print("\nSuggestions:")
            for s in validation_report.feedback.suggestions:
                print(f"  → {s}")

        header = master_resume.header.model_copy()
        header.location = job_details.location
        final_resume = Resume(header=header, resume_content=resume_content)

        print("\n" + "=" * 80)
        print("GENERATING LATEX")
        print("=" * 80)
        file_path = generate_latex_resume(final_resume, job_details)
        print(f"✓ {file_path}")

        track_application(job_details)

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except SystemExit:
        raise
    except Exception as e:
        print(f"✗ {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()
