from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.intelligence import assess_project, change_impact, milestone_forecast, portfolio, retrieve
from app.models import Blocker, Dependency, KPI, Milestone, Project
from app.seed import seed_demo


def memory_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return Session(engine)


def test_risk_score_is_deterministic_and_evidence_backed():
    today = date(2026, 9, 30)
    project = Project(name="Test", client="Client", owner="Owner", target_date=today + timedelta(days=30),
                      budget=100, spend=100, teams=[], systems=[], workflows=[])
    project.milestones.append(Milestone(title="API migration", due_date=today - timedelta(days=6), progress=61))
    project.blockers.extend(Blocker(title=f"Blocker {n}", severity="high") for n in range(3))
    project.kpis.append(KPI(name="Testing", actual=61, target=80, unit="%", direction="higher"))
    project.dependencies.append(Dependency(name="Payment API", slipped_count=2))
    result = assess_project(project, today)
    assert result["score"] == 86
    assert result["status"] == "critical"
    assert {item["type"] for item in result["evidence"]} == {"milestone", "blocker", "kpi", "dependency"}
    assert result == assess_project(project, today)
    project.milestones[0].status = "done"
    assert assess_project(project, today)["score"] == 62
    project.kpis[0].previous_actual = 90
    assert assess_project(project, today)["score"] > 62


def test_seeded_portfolio_and_change_impact():
    with memory_db() as db:
        seed_demo(db)
        summary = portfolio(db)
        assert (summary["total"], summary["on_track"], summary["at_risk"], summary["critical"]) == (12, 8, 3, 1)
        impact = change_impact(db, "Move customer support from Salesforce to a new platform")
        assert {p["project"] for p in impact["affected_projects"]} >= {
            "Customer Data Migration", "Support Platform Transition"}
        assert "Customer Support" in impact["affected_teams"]
        assert any("Salesforce" in d["name"] for d in impact["high_risk_dependencies"])
        assert retrieve(db, "Why is Project Phoenix delayed?")[0]["project"] == "Project Phoenix"
        assert any(item["classification"] == "overdue" for item in milestone_forecast(db))
