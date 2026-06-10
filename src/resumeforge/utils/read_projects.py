import json
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
