import json
import re
from pathlib import Path

from resumeforge.config import PROJECTS_DIR
from resumeforge.models import MasterProject


def read_projects() -> list[MasterProject]:
    if not PROJECTS_DIR.exists():
        return []
    projects = []
    for path in sorted(PROJECTS_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            projects.append(MasterProject.model_validate(data))
        except Exception as e:
            raise ValueError(f"Failed to parse {path.name}: {e}") from e
    return projects


def save_project(project: MasterProject) -> Path:
    """Write a project to data/projects/<slug>.json, avoiding name collisions."""
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", project.name.lower()).strip("-") or "project"
    path = PROJECTS_DIR / f"{slug}.json"
    counter = 2
    while path.exists():
        path = PROJECTS_DIR / f"{slug}-{counter}.json"
        counter += 1
    path.write_text(json.dumps(project.model_dump(), indent=2), encoding="utf-8")
    return path
