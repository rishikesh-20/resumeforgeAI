#!/usr/bin/env python
import sys
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from resumeforge.models import JobDetails
from resumeforge.pipeline import run_pipeline
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

        print()
        result = run_pipeline(job_details, on_stage=print)
        validation_report = result.validation_report

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

        print(f"\n✓ {result.tex_path}")

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
