import os
import json
import time
import yaml
from pathlib import Path
from google import genai
from google.genai import types
import ollama as _ollama

from resumeforge.models import JobAnalysis, ResumeContent, ResumeValidationReport

_CONFIG_DIR = Path(__file__).parent / "config"


def _load_system_prompt(agent_name: str) -> str:
    with open(_CONFIG_DIR / "agents.yaml") as f:
        cfg = yaml.safe_load(f)[agent_name]
    return f"{cfg['role']}\n\n{cfg['goal']}\n\n{cfg['backstory']}"


def _load_task(task_name: str) -> str:
    with open(_CONFIG_DIR / "tasks.yaml") as f:
        return yaml.safe_load(f)[task_name]["description"]


def _gemini() -> genai.Client:
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


def _gemini_with_retry(client: genai.Client, **kwargs):
    delays = [5, 15, 30]
    for i, delay in enumerate(delays):
        try:
            return client.models.generate_content(**kwargs)
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e) or "429" in str(e):
                if i < len(delays) - 1:
                    print(f"  Gemini busy, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
            raise
    return client.models.generate_content(**kwargs)


def run_job_analyst(job_description: str) -> JobAnalysis:
    task = _load_task("job_analysis_task").replace("{job_description}", job_description)
    client = _gemini()
    response = _gemini_with_retry(
        client,
        model="gemini-2.5-flash",
        contents=task,
        config=types.GenerateContentConfig(
            system_instruction=_load_system_prompt("job_analyst"),
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=JobAnalysis,
        ),
    )
    return JobAnalysis.model_validate_json(response.text)


def run_resume_tailor(master_resume: dict, all_projects: list, job_analysis: JobAnalysis) -> ResumeContent:
    task_template = _load_task("resume_tailoring_task")
    task = task_template.replace("{master_resume}", json.dumps(master_resume, indent=2))
    task = task.replace("{all_projects}", json.dumps([p if isinstance(p, dict) else p.model_dump() for p in all_projects], indent=2))
    user_message = (
        f"Job Analysis:\n{job_analysis.model_dump_json(indent=2)}\n\n{task}"
    )
    response = _ollama.chat(
        model="qwen3:14b",
        messages=[
            {"role": "system", "content": _load_system_prompt("resume_tailor")},
            {"role": "user", "content": user_message},
        ],
        format=ResumeContent.model_json_schema(),
        think=False,
        options={"temperature": 0.5},
    )
    return ResumeContent.model_validate_json(response.message.content)


def run_resume_validator(
    job_analysis: JobAnalysis, resume_content: ResumeContent
) -> ResumeValidationReport:
    task = _load_task("resume_validation_task")
    context = (
        f"Job Analysis:\n{job_analysis.model_dump_json(indent=2)}\n\n"
        f"Tailored Resume:\n{resume_content.model_dump_json(indent=2)}\n\n"
        f"{task}"
    )
    client = _gemini()
    response = _gemini_with_retry(
        client,
        model="gemini-2.5-flash",
        contents=context,
        config=types.GenerateContentConfig(
            system_instruction=_load_system_prompt("resume_validator"),
            temperature=0.2,
            response_mime_type="application/json",
            response_schema=ResumeValidationReport,
        ),
    )
    return ResumeValidationReport.model_validate_json(response.text)
