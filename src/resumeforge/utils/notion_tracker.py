import os
import logging
from datetime import datetime
from resumeforge.models import JobDetails

logger = logging.getLogger(__name__)


def track_application(job_details: JobDetails) -> None:
    """Log job application to Notion. Falls back to Google Sheets if Notion is unavailable."""
    if os.getenv("NOTION_API_KEY") and os.getenv("NOTION_DATABASE_ID"):
        try:
            _track_notion(job_details)
            print("✓ Job application logged to Notion")
            return
        except Exception as e:
            print(f"⚠ Notion tracking failed: {e}")



def _track_notion(job_details: JobDetails) -> None:
    from notion_client import Client

    notion = Client(auth=os.getenv("NOTION_API_KEY"))
    database_id = os.getenv("NOTION_DATABASE_ID")

    iso_date = datetime.strptime(job_details.date_applied, "%m-%d-%Y").strftime("%Y-%m-%d")

    # Chunk job description into ≤2000-char blocks (Notion API limit)
    desc = job_details.job_description
    chunks = [desc[i:i+2000] for i in range(0, len(desc), 2000)]
    children = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"type": "text", "text": {"content": chunk}}]},
        }
        for chunk in chunks
    ]

    notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": f"{job_details.company_name} — {job_details.job_title}"}}]},
            "Company": {"rich_text": [{"text": {"content": job_details.company_name}}]},
            "Role": {"rich_text": [{"text": {"content": job_details.job_title}}]},
            "Location": {"rich_text": [{"text": {"content": job_details.location}}]},
            "Date Applied": {"date": {"start": iso_date}},
            "Status": {"select": {"name": "Applied"}},
            "Job ID": {"rich_text": [{"text": {"content": job_details.job_id or ""}}]},
        },
        children=children,
    )


def _track_sheets(job_details: JobDetails) -> None:
    from resumeforge.utils.google_sheets import initialize_sheets_client

    client = initialize_sheets_client()
    client.append_row([
        job_details.date_applied,
        job_details.company_name,
        job_details.job_title,
        job_details.location,
        job_details.job_id or "",
        job_details.job_description,
        "Applied",
    ])
