from contextlib import asynccontextmanager
from datetime import date
from io import BytesIO
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import SessionLocal, get_db, init_db
from .intelligence import (
    ai_client, assess_project, change_impact, embed_texts, executive_brief, get_project,
    grounded_answer, note_signal, portfolio, project_view, projects_with_details, retrieve, split_text,
)
from .models import Blocker, Decision, Dependency, Document, DocumentChunk, KPI, Milestone, Note, Project
from .seed import seed_demo


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    with SessionLocal() as db:
        if not db.scalar(select(func.count(Project.id))):
            seed_demo(db)
    yield


app = FastAPI(title="Risk Intelligence", version="1.0.0", lifespan=lifespan)


class ProjectIn(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    client: str = Field(min_length=2, max_length=160)
    owner: str = Field(min_length=2, max_length=120)
    description: str = ""
    target_date: date
    budget: float = Field(default=0, ge=0)
    spend: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    teams: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)


class MilestoneIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    due_date: date
    progress: float = Field(default=0, ge=0, le=100)
    expected_progress: float = Field(default=100, ge=0, le=100)
    status: str = Field(default="open", pattern="^(open|done)$")


class ProjectUpdate(BaseModel):
    owner: str | None = Field(default=None, min_length=2, max_length=120)
    target_date: date | None = None
    budget: float | None = Field(default=None, ge=0)
    spend: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern="^[A-Z]{3}$")
    active: bool | None = None


class BlockerIn(BaseModel):
    title: str = Field(min_length=3, max_length=240)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")


class DependencyIn(BaseModel):
    name: str = Field(min_length=3, max_length=200)
    team: str = ""
    system: str = ""
    slipped_count: int = Field(default=0, ge=0)


class KPIIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    actual: float
    previous_actual: float | None = None
    target: float = Field(gt=0)
    unit: str = "%"
    direction: str = Field(default="higher", pattern="^(higher|lower)$")


class NoteIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    body: str = Field(min_length=3)
    signal: str | None = Field(default=None, pattern="^(negative|neutral|positive)$")
    happened_at: date = Field(default_factory=date.today)


class DecisionIn(BaseModel):
    summary: str = Field(min_length=3)
    decided_at: date = Field(default_factory=date.today)


class AskIn(BaseModel):
    question: str = Field(min_length=5, max_length=1000)
    project_id: int | None = None


class ImpactIn(BaseModel):
    announcement: str = Field(min_length=10, max_length=5000)


class DocumentIn(BaseModel):
    title: str = Field(min_length=3, max_length=220)
    content: str = Field(min_length=10, max_length=100000)
    source_type: str = "report"


def require_project(db: Session, project_id: int):
    project = get_project(db, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def add_document(db: Session, project_id: int, title: str, content: str, source_type: str):
    require_project(db, project_id)
    chunks = split_text(content)
    if not chunks:
        raise HTTPException(422, "Document has no extractable text")
    document = Document(project_id=project_id, title=title, source_type=source_type)
    db.add(document)
    db.flush()
    try:
        embeddings = embed_texts(chunks) if db.bind.dialect.name == "postgresql" else [None] * len(chunks)
    except Exception:
        embeddings = [None] * len(chunks)
    db.add_all(DocumentChunk(document_id=document.id, position=index, content=content,
                             embedding=embeddings[index]) for index, content in enumerate(chunks))
    db.commit()
    return {"id": document.id, "title": title, "chunks": len(chunks),
            "retrieval": "vector + keyword" if any(embeddings) else "keyword"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/portfolio")
def read_portfolio(db: Session = Depends(get_db)):
    return portfolio(db)


@app.get("/api/projects")
def list_projects(db: Session = Depends(get_db)):
    return [project_view(p) for p in projects_with_details(db)]


@app.post("/api/projects", status_code=201)
def create_project(data: ProjectIn, db: Session = Depends(get_db)):
    if db.scalar(select(Project.id).where(Project.name == data.name)):
        raise HTTPException(409, "A project with this name already exists")
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    return project_view(require_project(db, project.id), detail=True)


@app.get("/api/projects/{project_id}")
def read_project(project_id: int, db: Session = Depends(get_db)):
    return project_view(require_project(db, project_id), detail=True)


@app.patch("/api/projects/{project_id}")
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    project = require_project(db, project_id)
    changes = data.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise HTTPException(422, "Updated values cannot be null")
    for key, value in changes.items():
        setattr(project, key, value)
    db.commit()
    return project_view(require_project(db, project_id), detail=True)


@app.post("/api/projects/{project_id}/milestones", status_code=201)
def create_milestone(project_id: int, data: MilestoneIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    row = Milestone(project_id=project_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@app.patch("/api/milestones/{milestone_id}")
def update_milestone(milestone_id: int, data: MilestoneIn, db: Session = Depends(get_db)):
    row = db.get(Milestone, milestone_id)
    if not row:
        raise HTTPException(404, "Milestone not found")
    for key, value in data.model_dump().items():
        setattr(row, key, value)
    db.commit()
    return {"id": row.id}


@app.post("/api/projects/{project_id}/blockers", status_code=201)
def create_blocker(project_id: int, data: BlockerIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    row = Blocker(project_id=project_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@app.patch("/api/blockers/{blocker_id}/resolve")
def resolve_blocker(blocker_id: int, db: Session = Depends(get_db)):
    row = db.get(Blocker, blocker_id)
    if not row:
        raise HTTPException(404, "Blocker not found")
    row.resolved = True
    db.commit()
    return {"id": row.id, "resolved": True}


@app.post("/api/projects/{project_id}/dependencies", status_code=201)
def create_dependency(project_id: int, data: DependencyIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    row = Dependency(project_id=project_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@app.post("/api/projects/{project_id}/kpis", status_code=201)
def create_kpi(project_id: int, data: KPIIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    row = KPI(project_id=project_id, **data.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id}


@app.post("/api/projects/{project_id}/notes", status_code=201)
def create_note(project_id: int, data: NoteIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    payload = data.model_dump()
    payload["signal"] = payload["signal"] or note_signal(payload["body"])
    row = Note(project_id=project_id, **payload)
    db.add(row)
    db.commit()
    add_document(db, project_id, data.title, data.body, "meeting note")
    return {"id": row.id, "signal": row.signal}


@app.post("/api/projects/{project_id}/decisions", status_code=201)
def create_decision(project_id: int, data: DecisionIn, db: Session = Depends(get_db)):
    require_project(db, project_id)
    row = Decision(project_id=project_id, **data.model_dump())
    db.add(row)
    db.commit()
    add_document(db, project_id, f"Decision {data.decided_at.isoformat()}", data.summary, "decision")
    return {"id": row.id}


@app.post("/api/projects/{project_id}/documents", status_code=201)
def create_document(project_id: int, data: DocumentIn, db: Session = Depends(get_db)):
    return add_document(db, project_id, data.title, data.content, data.source_type)


@app.post("/api/projects/{project_id}/upload", status_code=201)
async def upload_document(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".csv", ".pdf"}:
        raise HTTPException(415, "Upload a PDF, TXT, MD, or CSV file")
    raw = await file.read(5_000_001)
    if len(raw) > 5_000_000:
        raise HTTPException(413, "Maximum file size is 5 MB")
    try:
        if suffix == ".pdf":
            from pypdf import PdfReader
            content = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
        else:
            content = raw.decode("utf-8-sig")
    except Exception as exc:
        raise HTTPException(422, "Unable to extract text from this file") from exc
    return add_document(db, project_id, Path(file.filename).name, content, suffix.lstrip("."))


@app.get("/api/briefing")
def read_briefing(db: Session = Depends(get_db)):
    return executive_brief(db)


@app.get("/api/milestones/forecast")
def read_forecast(db: Session = Depends(get_db)):
    from .intelligence import milestone_forecast
    return milestone_forecast(db)


@app.post("/api/projects/{project_id}/explain")
def explain_risk(project_id: int, db: Session = Depends(get_db)):
    from .intelligence import explain_project
    return explain_project(require_project(db, project_id))


@app.post("/api/ask")
def ask(data: AskIn, db: Session = Depends(get_db)):
    if data.project_id:
        require_project(db, data.project_id)
    evidence = retrieve(db, data.question, data.project_id)
    return grounded_answer(data.question, evidence)


@app.post("/api/change-impact")
def analyze_change(data: ImpactIn, db: Session = Depends(get_db)):
    return change_impact(db, data.announcement)


STATIC = Path(__file__).resolve().parent.parent / "web"
app.mount("/assets", StaticFiles(directory=STATIC), name="assets")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
