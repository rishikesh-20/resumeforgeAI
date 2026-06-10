import json
from resumeforge.models import MasterResume
from resumeforge.config import RESUME_PATH
from resumeforge.exceptions import DataLoadError


def read_resume_json() -> MasterResume:
    """
    Read resume.json from the data directory and return as MasterResume model.

    Returns:
        MasterResume: Parsed resume data containing header and content

    Raises:
        DataLoadError: If resume.json does not exist, is invalid, or doesn't match schema
    """
    try:
        if not RESUME_PATH.exists():
            raise DataLoadError(
                "resume.json not found. Copy the example and fill in your details:\n"
                "  cp data/resume.json.example data/resume.json"
            )

        with open(RESUME_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        return MasterResume(**data)
    except (json.JSONDecodeError, ValueError) as e:
        raise DataLoadError(f"Failed to parse resume.json: {e}") from e
    except Exception as e:
        raise DataLoadError(f"Failed to read resume.json: {e}") from e
