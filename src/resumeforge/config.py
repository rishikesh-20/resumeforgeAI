"""Centralized configuration for file paths and constants."""

from pathlib import Path

# Project root directory (3 levels up from this file: src/resumeforge/config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RESUME_PATH = DATA_DIR / "resume.json"
PROJECTS_DIR = DATA_DIR / "projects"

# Output directories
RESUMES_DIR = PROJECT_ROOT / "resumes"

# Template directories
TEMPLATES_DIR = PROJECT_ROOT / "templates"
RESUME_WORD_TEMPLATE = TEMPLATES_DIR / "resume_word_template.docx"
RESUME_LATEX_TEMPLATE = TEMPLATES_DIR / "resume_latex_template.tex"

# LaTeX resume output directory
RESUMES_TEX_DIR = PROJECT_ROOT / "resumestex"

