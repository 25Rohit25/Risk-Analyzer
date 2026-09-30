# Northstar Risk Intelligence

An evidence-first portfolio monitor for consulting and enterprise delivery teams. It turns project records and source documents into auditable risk assessments, an executive briefing, project Q&A, and change-impact analysis.

The repository includes **synthetic demonstration data**. It is a runnable prototype, not a production multi-tenant service.

## Run locally

Requires Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.api:app --reload
```

Open <http://127.0.0.1:8000>. The first run creates `risk.db` and seeds 12 sample initiatives. The UI and API share one server; interactive API documentation is at <http://127.0.0.1:8000/docs>.

For macOS/Linux, activate with `source .venv/bin/activate`.

## PostgreSQL and pgvector

```powershell
docker compose up -d db
$env:DATABASE_URL="postgresql+psycopg://risk:risk@localhost:5432/risk_intelligence"
uvicorn app.api:app --reload
```

The app creates the `vector` extension and an HNSW cosine index on document chunks. Set `OPENAI_API_KEY` to generate embeddings for **new** documents and use vector search. Documents ingested without a key remain searchable through keyword retrieval. For a fresh seeded database, the four demonstration reports are indexed as text; upload or paste a document with a key configured to exercise vector retrieval.

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-6-astra"  # optional
```

AI explanations use the [OpenAI Responses API](https://developers.openai.com/api/docs/guides/text); embeddings use [`text-embedding-3-small`](https://developers.openai.com/api/docs/guides/embeddings). Without an API key, the app still calculates scores, builds briefings, performs change matching, and returns retrieved evidence. The API key is read server-side only. Do not enter client information unless your organization's data handling rules permit the configured provider.

## What it does

| Workflow | Evidence and output |
| --- | --- |
| Portfolio | Owners, clients, target dates, budgets, milestones, blockers, dependencies, KPIs, status |
| Risk assessment | Deterministic score, contribution categories, source IDs, recommended actions |
| Executive briefing | Live counts, key developments, management attention, copyable summary |
| Ask intelligence | Chunked document retrieval with source excerpts; optional grounded AI response |
| Change impact | Matches announcement terms to systems, workflows, dependencies, and documents; reports affected teams and actions |
| Milestone forecast | Flags overdue work or a progress gap on milestones due within 14 days |

### Risk scoring

Each signal contributes points with category caps. The score is the capped sum, from 0 to 100. The model does not set or edit it.

| Indicator | Calculation | Cap |
| --- | --- | ---: |
| Milestones | Overdue: 12 points plus 2 per overdue day, up to 28. Due within 14 days and behind expected progress: 4–12 points. | 30 |
| Open blockers | High 10, medium 5, low 2 | 30 |
| KPI gap and trend | Relative target gap × 85, minimum 4 when below target. A drop from previous actual adds 2–8. | 22 |
| Slipped dependencies | 6 plus 3 per slip | 16 |
| Budget overrun | Relative overrun × 40, minimum 3 | 10 |
| Negative meeting signals | 4 per negative note | 8 |

Scores **0–34** are on track, **35–74** are at risk, and **75–100** are critical. The UI shows the underlying evidence and category contribution. These weights are illustrative and should be calibrated with real historical outcomes before operational use.

### Document pipeline

Upload PDF, TXT, MD, or CSV files up to 5 MB, or paste document text. Content is normalized and split into overlapping chunks. On PostgreSQL with an API key, new chunks receive 1536-dimensional embeddings stored in pgvector. Otherwise, retrieval uses keyword matching. Answers include the actual excerpts used. Image-only PDFs need OCR before upload.

### Change-impact method

The analyzer matches non-generic terms in an announcement against active projects' system, workflow, dependency, and document records. It returns matching terms and affected projects, then aggregates their teams and systems. This is an evidence search, not a claim that every downstream dependency has been discovered. Review the result before using it as a change plan.

## API

Key endpoints:

- `GET /api/portfolio`, `GET /api/projects/{id}`, `GET /api/briefing`, `GET /api/milestones/forecast`
- `POST /api/projects`, `POST /api/projects/{id}/milestones|blockers|dependencies|kpis|notes|decisions|documents`
- `POST /api/projects/{id}/upload`
- `PATCH /api/milestones/{id}`, `PATCH /api/blockers/{id}/resolve`
- `PATCH /api/projects/{id}` to update owner, target date, budget, spend, currency, or active state
- `POST /api/ask`, `POST /api/change-impact`
- `POST /api/projects/{id}/explain` for an optional AI-assisted risk narrative with the deterministic score held fixed

FastAPI's `/docs` shows request schemas and lets you try every route.

## Tests

```powershell
python -m pytest -q
```

## Deployment considerations

The prototype has no login, access control, tenant isolation, audit trail, background ingestion queue, or migration system. Add these before connecting real client data. For production, pin dependencies, manage secrets outside the repository, use HTTPS, set per-tenant document filters, and calibrate the risk model with project outcomes. Uploaded files are extracted in memory; their source bytes are not retained.
