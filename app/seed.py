"""Clearly synthetic portfolio data for first-run evaluation."""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .intelligence import split_text
from .models import Blocker, Decision, Dependency, Document, DocumentChunk, KPI, Milestone, Note, Project


def seed_demo(db: Session):
    today = date.today()
    plus = lambda days: today + timedelta(days=days)
    specs = [
        ("Project Phoenix", "Aster Financial", "Maya Iyer", "Modernize payment orchestration and retire the legacy API gateway.",
         ["Payments", "Platform Engineering", "Quality Assurance"], ["Payment API", "API Gateway"], ["Settlement", "Checkout"], 45),
        ("Customer Data Migration", "Northstar Retail", "Owen Brooks", "Unify customer records and move analytics to a governed data foundation.",
         ["Data Engineering", "Sales Operations", "Customer Support"], ["Salesforce CRM", "Customer Analytics", "ETL Pipeline"], ["Customer onboarding", "Reporting"], 62),
        ("ERP Transformation", "Meridian Group", "Priya Shah", "Consolidate finance operations onto a new enterprise resource platform.",
         ["Finance", "Procurement", "IT Operations"], ["ERP Core", "Finance Reporting"], ["Purchase to pay", "Month-end close"], 95),
        ("Support Platform Transition", "Northstar Retail", "Elena Torres", "Move service operations to a unified support platform.",
         ["Customer Support", "Sales Operations", "Data Engineering"], ["Salesforce CRM", "CRM Integration", "Reporting Pipeline"], ["Case routing", "Customer support"], 78),
        ("Cloud Cost Optimization", "Aster Financial", "Noah Patel", "Improve cloud unit economics while maintaining service quality.",
         ["Cloud Operations", "Finance"], ["Cloud Billing", "FinOps Dashboard"], ["Cost allocation"], 40),
        ("Digital Claims", "Harbor Insurance", "Amira Khan", "Digitize claims intake and case handling.",
         ["Claims", "Product", "Engineering"], ["Claims Portal"], ["Claims intake"], 90),
        ("Workforce Analytics", "Meridian Group", "Luca Martin", "Establish reliable workforce reporting for HR leaders.",
         ["People Analytics", "HR"], ["HRIS", "Workforce BI"], ["Headcount reporting"], 55),
        ("Supplier Onboarding", "Meridian Group", "Sara Chen", "Standardize supplier controls and onboarding.",
         ["Procurement", "Compliance"], ["Supplier Portal"], ["Vendor approval"], 65),
        ("Channel Experience", "Harbor Insurance", "Ava Morgan", "Improve broker self-service and digital adoption.",
         ["Distribution", "Product"], ["Broker Portal"], ["Broker onboarding"], 70),
        ("Pricing Governance", "Aster Financial", "Daniel Lee", "Introduce transparent approval and monitoring for pricing changes.",
         ["Pricing", "Risk"], ["Pricing Engine"], ["Price approval"], 56),
        ("Identity Consolidation", "Northstar Retail", "Ravi Nair", "Consolidate internal identity services and access policy.",
         ["Security", "IT Operations"], ["Identity Provider"], ["Access review"], 67),
        ("Sustainability Reporting", "Harbor Insurance", "Grace Kim", "Create a traceable emissions reporting process.",
         ["Sustainability", "Finance"], ["ESG Data Hub"], ["Quarterly disclosure"], 110),
    ]
    projects = []
    for name, client, owner, description, teams, systems, workflows, target_days in specs:
        project = Project(name=name, client=client, owner=owner, description=description,
                          target_date=plus(target_days), budget=1_200_000, spend=780_000, currency="USD",
                          teams=teams, systems=systems, workflows=workflows)
        db.add(project)
        projects.append(project)
    db.flush()

    for project in projects:
        db.add(Milestone(project_id=project.id, title="Delivery checkpoint", due_date=plus(12),
                         progress=72, expected_progress=70))
        db.add(KPI(project_id=project.id, name="Delivery completion", actual=74, target=70, unit="%"))

    phoenix, customer, erp, support = projects[:4]
    db.add(Milestone(project_id=phoenix.id, title="API migration", due_date=plus(-6), progress=61, expected_progress=100))
    db.add(KPI(project_id=phoenix.id, name="Testing completion", actual=61, target=80, unit="%"))
    for title in ["Payment API contract unresolved", "QA environment unavailable", "Gateway test data incomplete"]:
        db.add(Blocker(project_id=phoenix.id, title=title, severity="high"))
    db.add(Dependency(project_id=phoenix.id, name="Payment API partner delivery", team="Platform Engineering",
                      system="Payment API", slipped_count=2))
    db.add(Note(project_id=phoenix.id, title="Weekly delivery review", signal="neutral", happened_at=plus(-2),
                body="The API integration is six days behind plan. Leadership agreed to escalate the partner dependency and reallocate two QA engineers."))
    db.add(Decision(project_id=phoenix.id, summary="Escalate the payment API partner and add two QA engineers to integration testing.", decided_at=plus(-2)))

    db.add(Milestone(project_id=customer.id, title="Historical record migration", due_date=plus(-2), progress=82))
    db.add(Blocker(project_id=customer.id, title="Duplicate account mappings require review", severity="high"))
    db.add(Dependency(project_id=customer.id, name="Salesforce API connector", team="Sales Operations",
                      system="Salesforce CRM", slipped_count=1))
    db.add(Note(project_id=customer.id, title="Data quality meeting", signal="neutral", happened_at=plus(-3),
                body="Sales Operations will validate account mappings before the next extraction. The Salesforce API connector needs retesting."))
    db.add(Decision(project_id=customer.id, summary="Retain historical CRM records in read-only storage for audit after cutover.", decided_at=plus(-3)))

    db.add(Milestone(project_id=erp.id, title="Finance integration test", due_date=plus(-1), progress=76))
    db.add(Blocker(project_id=erp.id, title="Procurement approval workflow pending", severity="medium"))
    db.add(Blocker(project_id=erp.id, title="Finance mapping defect awaiting vendor fix", severity="high"))
    db.add(KPI(project_id=erp.id, name="Integration tests passed", actual=71, target=80, unit="%"))

    db.add(Blocker(project_id=support.id, title="Training materials await process sign-off", severity="medium"))
    db.add(Blocker(project_id=support.id, title="Cutover rehearsal cannot start until export validation", severity="high"))
    db.add(KPI(project_id=support.id, name="Agent readiness", actual=66, target=80, unit="%"))
    db.add(Dependency(project_id=support.id, name="Salesforce case export", team="Data Engineering",
                      system="Salesforce CRM", slipped_count=1))
    db.add(Decision(project_id=support.id, summary="Train support supervisors first, then roll out to agents in two waves.", decided_at=plus(-4)))

    documents = [
        (phoenix, "Phoenix steering update", "Payment API integration has slipped six days. Testing completion is 61 percent against an 80 percent target. Three high priority blockers remain open: partner contract, QA environment, and gateway test data. Leadership decided to escalate the dependency and reallocate two QA engineers."),
        (customer, "Customer data migration report", "The historical record migration is overdue. Salesforce API connector delivery slipped once. Account mapping duplicates are unresolved. Sales Operations must validate source records. Historical CRM records will be retained read only for audit after cutover."),
        (erp, "ERP integration report", "Finance integration testing is behind schedule. Procurement approval workflow sign-off is pending. Integration tests passed are 71 percent against an 80 percent target."),
        (support, "Support change plan", "The Salesforce CRM case export feeds the CRM Integration service and Reporting Pipeline. Customer Support, Sales Operations, and Data Engineering need training and cutover communications. Supervisors will train before support agents."),
    ]
    db.flush()
    by_id = {project.id: project for project in projects}
    documents.extend((by_id[note.project_id], note.title, note.body) for note in db.scalars(select(Note)).all())
    documents.extend((by_id[decision.project_id], f"Decision {decision.decided_at.isoformat()}", decision.summary)
                     for decision in db.scalars(select(Decision)).all())
    for project, title, content in documents:
        document = Document(project_id=project.id, title=title, source_type="report")
        db.add(document)
        db.flush()
        for index, chunk in enumerate(split_text(content)):
            db.add(DocumentChunk(document_id=document.id, position=index, content=chunk))
    db.commit()
