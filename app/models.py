from datetime import date, datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    client: Mapped[str] = mapped_column(String(160))
    owner: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    target_date: Mapped[date] = mapped_column(Date)
    budget: Mapped[float] = mapped_column(Float, default=0)
    spend: Mapped[float] = mapped_column(Float, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    teams: Mapped[list] = mapped_column(JSON, default=list)
    systems: Mapped[list] = mapped_column(JSON, default=list)
    workflows: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    milestones = relationship("Milestone", cascade="all, delete-orphan", back_populates="project")
    blockers = relationship("Blocker", cascade="all, delete-orphan", back_populates="project")
    dependencies = relationship("Dependency", cascade="all, delete-orphan", back_populates="project")
    kpis = relationship("KPI", cascade="all, delete-orphan", back_populates="project")
    notes = relationship("Note", cascade="all, delete-orphan", back_populates="project")
    decisions = relationship("Decision", cascade="all, delete-orphan", back_populates="project")
    documents = relationship("Document", cascade="all, delete-orphan", back_populates="project")


class Milestone(Base):
    __tablename__ = "milestones"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    due_date: Mapped[date] = mapped_column(Date)
    progress: Mapped[float] = mapped_column(Float, default=0)
    expected_progress: Mapped[float] = mapped_column(Float, default=100)
    status: Mapped[str] = mapped_column(String(24), default="open")
    project = relationship("Project", back_populates="milestones")


class Blocker(Base):
    __tablename__ = "blockers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    severity: Mapped[str] = mapped_column(String(16), default="medium")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    project = relationship("Project", back_populates="blockers")


class Dependency(Base):
    __tablename__ = "dependencies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    team: Mapped[str] = mapped_column(String(120), default="")
    system: Mapped[str] = mapped_column(String(120), default="")
    slipped_count: Mapped[int] = mapped_column(Integer, default=0)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    project = relationship("Project", back_populates="dependencies")


class KPI(Base):
    __tablename__ = "kpis"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    actual: Mapped[float] = mapped_column(Float)
    previous_actual: Mapped[float | None] = mapped_column(Float, nullable=True)
    target: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(24), default="%")
    direction: Mapped[str] = mapped_column(String(12), default="higher")
    project = relationship("Project", back_populates="kpis")


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    signal: Mapped[str] = mapped_column(String(16), default="neutral")
    happened_at: Mapped[date] = mapped_column(Date, default=date.today)
    project = relationship("Project", back_populates="notes")


class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[date] = mapped_column(Date, default=date.today)
    project = relationship("Project", back_populates="decisions")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(220))
    source_type: Mapped[str] = mapped_column(String(32), default="report")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", cascade="all, delete-orphan", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list | None] = mapped_column(Vector(1536).with_variant(JSON, "sqlite"), nullable=True)
    document = relationship("Document", back_populates="chunks")
