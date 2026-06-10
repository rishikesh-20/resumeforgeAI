from jinja2 import Environment, FileSystemLoader
from resumeforge.models import Resume, JobDetails
from resumeforge.config import RESUMES_TEX_DIR, RESUME_LATEX_TEMPLATE


def _latex_escape(text: str) -> str:
    chars = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(chars.get(c, c) for c in str(text))


def generate_latex_resume(resume: Resume, job_details: JobDetails) -> str:
    """Generate a .tex file from Resume and JobDetails. Returns the file path."""
    RESUMES_TEX_DIR.mkdir(parents=True, exist_ok=True)

    company = job_details.company_name.replace(" ", "_").replace("/", "_")
    role = job_details.job_title.replace(" ", "_").replace("/", "_")
    file_path = RESUMES_TEX_DIR / f"{company}_{role}.tex"

    env = Environment(
        loader=FileSystemLoader(str(RESUME_LATEX_TEMPLATE.parent)),
        block_start_string="(%",
        block_end_string="%)",
        variable_start_string="((",
        variable_end_string="))",
        comment_start_string="(#",
        comment_end_string="#)",
        autoescape=False,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["le"] = _latex_escape

    template = env.get_template(RESUME_LATEX_TEMPLATE.name)
    rendered = template.render(
        header=resume.header,
        resume_content=resume.resume_content,
    )

    file_path.write_text(rendered, encoding="utf-8")
    return str(file_path)
