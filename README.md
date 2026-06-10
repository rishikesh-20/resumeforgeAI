# ResumeForge AI

An AI-powered resume tailoring system that analyzes job descriptions and generates a customized, ATS-optimized LaTeX resume — ready to compile and submit.

## How it works

Three specialized AI agents run sequentially:

| Agent | Model | Role |
|---|---|---|
| Job Analyst | Gemini 2.5 Flash (free tier) | Extracts skills, requirements, tone, and cultural signals from the job description |
| Resume Tailor | Qwen3:14b (local via Ollama) | Selects the most relevant projects from your pool, rewrites bullets with job-specific keywords, and enforces a one-page budget |
| Resume Validator | Gemini 2.5 Flash (free tier) | Scores ATS compatibility, keyword integration rate, and human readability before generating output |

Resume tailoring runs fully locally (Ollama) — your resume data never leaves your machine for the creative step. Gemini free tier handles the structured extraction tasks.

## Output

- **LaTeX file** saved to `resumestex/{Company}_{Role}.tex` — compile with `pdflatex` or Overleaf
- **Validation report** printed to terminal with ATS score, keyword integration rate, and suggestions
- **Application log** added to your Notion database with the full job description saved for interview prep

## Setup

### 1. Prerequisites

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) — `pip install uv`
- [Ollama](https://ollama.com) with `qwen3:14b` pulled: `ollama pull qwen3:14b`

### 2. Install

```bash
git clone https://github.com/rishikesh-20/resumeforge.git
cd resumeforge
uv sync
```

### 3. Environment variables

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

Then edit `.env`:

```env
GOOGLE_API_KEY=your_google_ai_studio_key
NOTION_API_KEY=your_notion_integration_key
NOTION_DATABASE_ID=your_notion_database_id
```

**Getting these keys:**
- `GOOGLE_API_KEY` — [Google AI Studio](https://aistudio.google.com) → Get API key (free)
- `NOTION_API_KEY` — [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration → copy secret
- `NOTION_DATABASE_ID` — The ID from your Notion database URL: `notion.so/{workspace}/{DATABASE_ID}?v=...`

### 4. Notion database setup

**Step 1 — Create an integration**

Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration → give it a name → Submit. Copy the **Internal Integration Secret** — this is your `NOTION_API_KEY`.

**Step 2 — Create a database**

Create a new full-page database in Notion with exactly these properties:

| Property | Type |
|---|---|
| Name | Title |
| Company | Text |
| Role | Text |
| Location | Text |
| Date Applied | Date |
| Status | Select — add options: `Applied`, `Interview`, `Offer`, `Rejected` |
| Job ID | Text |

**Step 3 — Get the database ID**

Open the database in Notion. The URL looks like:
```
https://www.notion.so/{workspace}/{DATABASE_ID}?v=...
```
Copy the `DATABASE_ID` part (32-character string before `?v=`) — this is your `NOTION_DATABASE_ID`.

**Step 4 — Connect the integration to the database**

Open the database → click `...` (top right) → Connections → search for your integration → click Connect. Without this step, the API key alone won't work.

### 5. Add your resume data

Copy the example and fill in your details:

```bash
cp data/resume.json.example data/resume.json
```

Edit `data/resume.json` with your actual header, work experience, education, and skills.

### 6. Add your projects

Projects live in `data/projects/` as individual JSON files — one file per project. Copy the example to get started:

```bash
cp data/projects/project.json.example data/projects/my-project.json
```

Add as many projects as you have. For each run, the AI scores all projects against the job description and selects the top 3 most relevant ones. The `description` field should be a detailed paragraph — the more context you give, the better the AI can tailor the bullet points.

**Example project file:**
```json
{
  "name": "My Project",
  "tech_stack": "Python, FastAPI, PostgreSQL",
  "date": "December 2024",
  "description": "Detailed paragraph about what you built, why, how, and any results or metrics..."
}
```

## Usage

```bash
uv run resumeforge
```

You will be prompted for:
- Company name, job title, location, job ID (optional)
- Job description (paste and type `END` on a new line to finish)

The three agents run sequentially (~3–6 minutes total, mostly the local Ollama step), then the `.tex` file is saved to `resumestex/` and the application is logged to Notion with the full job description.

## Compiling to PDF

Once you have a `.tex` file:

```bash
pdflatex resumestex/Company_Role.tex
```

Or paste the contents into [Overleaf](https://overleaf.com) for online compilation.

## Customizing the LaTeX template

The template is at `templates/resume_latex_template.tex`. It uses Jinja2 with `(( ))` for variables and `(% %)` for blocks (to avoid conflicts with LaTeX syntax). Edit the static sections (certifications, formatting, margins) directly. Preserve the `(( ))` and `(% %)` placeholders.

## Project structure

```
resumeforge/
├── data/
│   ├── resume.json               # Your master resume (gitignored — copy from resume.json.example)
│   ├── resume.json.example       # Template to copy and fill in
│   └── projects/                 # One JSON file per project (gitignored)
│       └── project.json.example  # Template to copy for each project
├── resumestex/                   # Generated .tex files (gitignored)
├── templates/
│   └── resume_latex_template.tex # Jinja2 LaTeX template
└── src/resumeforge/
    ├── config/
    │   ├── agents.yaml           # Agent roles and backstories
    │   └── tasks.yaml            # Task instructions
    ├── utils/
    │   ├── resume_latex_generator.py
    │   ├── notion_tracker.py
    │   ├── read_projects.py      # Loads all projects from data/projects/
    │   └── ...
    ├── agents.py                 # Agent and task definitions
    ├── models.py                 # Pydantic data models
    └── main.py                   # Entry point
```

## Built with

- [Qwen3:14b via Ollama](https://ollama.com) — local LLM for resume tailoring
- [Gemini 2.5 Flash](https://aistudio.google.com) — free-tier LLM for analysis and validation
- [Jinja2](https://jinja.palletsprojects.com) — LaTeX template rendering
- [notion-client](https://github.com/ramnes/notion-sdk-py) — application tracking
