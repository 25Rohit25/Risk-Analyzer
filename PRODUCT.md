# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Inferred while the stack question is open: FastAPI, SQLAlchemy, PostgreSQL with pgvector, and a dependency-light web UI. SQLite supports a quick local demo.

## Users

Consulting and enterprise delivery teams monitoring multiple client initiatives. Leadership needs a concise cross-portfolio view with evidence for follow-up.

## Product Purpose

Consolidate structured delivery signals and documents so teams can identify at-risk initiatives, explain delays, answer project questions, and prepare management briefings.

## Positioning

Risk scores come from transparent, deterministic indicators. The optional AI layer explains retrieved evidence without setting the score.

## Operating Context

Teams ingest milestone plans, KPI updates, blockers, dependencies, meeting notes, decisions, and reports. They review a portfolio dashboard, investigate projects, produce a weekly brief, and assess proposed organizational changes.

## Capabilities and Constraints

The first version supports manual entry and PDF/TXT/MD/CSV upload. PostgreSQL with pgvector enables semantic document search when embeddings are configured. SQLite uses keyword retrieval for a zero-setup demo. No enterprise identity provider, tenant isolation, or automated third-party connectors are specified in the brief; these are open decisions for deployment.

## Evidence on Hand

The repository was empty. The app includes clearly synthetic sample projects for evaluation; no client data or performance claims were supplied.

## Product Principles

- Every risk finding points to a project signal.
- Management summaries remain concise and actionable.
- Change impact shows which metadata or document text created a match.
- A missing AI key never blocks core portfolio workflows.
