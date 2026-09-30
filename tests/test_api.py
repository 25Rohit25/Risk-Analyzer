from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import app
from app.db import Base, get_db


def test_project_document_question_and_impact_flow(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        client = TestClient(app)
        created = client.post("/api/projects", json={"name": "Support migration", "client": "Client A",
            "owner": "Maya", "target_date": (date.today() + timedelta(days=30)).isoformat(),
            "teams": ["Customer Support"], "systems": ["Salesforce CRM"], "workflows": ["Case routing"]})
        assert created.status_code == 201, created.text
        project_id = created.json()["id"]
        uploaded = client.post(f"/api/projects/{project_id}/documents", json={"title": "Cutover note",
            "content": "The Salesforce CRM case export is delayed. Customer Support needs role-based training before cutover."})
        assert uploaded.status_code == 201, uploaded.text
        answer = client.post("/api/ask", json={"question": "Why is the Salesforce case export delayed?", "project_id": project_id})
        assert answer.status_code == 200, answer.text
        assert answer.json()["sources"][0]["title"] == "Cutover note"
        impact = client.post("/api/change-impact", json={"announcement": "Replace Salesforce customer support platform"})
        assert impact.status_code == 200, impact.text
        assert impact.json()["affected_projects"][0]["project"] == "Support migration"
        updated = client.patch(f"/api/projects/{project_id}", json={"budget": 100, "spend": 150})
        assert updated.status_code == 200, updated.text
        assert updated.json()["risk"]["contributions"]["budget"] == 10
    finally:
        app.dependency_overrides.clear()
