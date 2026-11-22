# 20 — Team Responsibilities & Ownership Matrix

**Purpose:** Document role ownership, domain boundaries, review gates, and handoffs across the four-person founding team as approved in the *MVP Feature Plan by Domain (19 Nov 2026)*.

---

## 1. Team Ownership Split

| Person | Role | Domains Owned | Core MVP Deliverables |
|---|---|---|---|
| **Person 1** | Scientific Lead | **Domain A:** Bioprocess Science & Engineering | Unit registry (`pint`), formula library (`scalebridge_science.formulas`), calculation provenance, golden test vectors, scale-up risk engine, and `thresholds.yaml`. |
| **Person 2** | Backend Platform Lead | **Domain D:** Platform & Backend | Database schema and migrations (SQLAlchemy 2, Alembic), authentication & roles (JWT, Argon2id), tenant isolation, Process Passport, vessels, scenarios, REST API contract, audit log. |
| **Person 3** | Data & Readiness Lead | **Domain B:** Data & Ingestion<br/>**Domain C:** Decision Support | CSV/XLSX upload and mapping, unit normalisation on import, data-quality checks, equipment compatibility engine, validation planner, assessment orchestration. |
| **Person 4** | Reporting, DevOps & Quality Lead | **Domain E:** Reporting<br/>**Domain F:** Infrastructure, Security & Quality | Process-Transfer PDF Report generation (ReportLab), synthetic demo watermark & disclaimers, report regeneration & download, Docker & Docker Compose, Render hosting (`render.yaml`), GitHub Actions CI, backups, test strategy. |

---

## 2. Critical Handoffs

```
[Person 1: Science] ──────(Formula & Risk Interfaces)──────► [Person 3: Decision Support]
       │                                                                  │
       │                                                       (Stored Assessment)
       ▼                                                                  ▼
[Person 2: Backend Platform] ◄──(CI / Deployment Pipeline)─── [Person 4: Reporting & DevOps]
```

1. **Person 1 to Person 3:** Formula and risk function interfaces. Agreed first so assessment orchestration could be built against well-typed stubs.
2. **Person 2 to Everyone:** Database schema and REST API contracts. Frozen early so other domains and the frontend build against an immutable contract.
3. **Person 3 to Person 4:** Stored assessment data structure, which forms the single source of truth for the PDF Process-Transfer Report.
4. **Person 4 to Everyone:** The continuous integration (CI) pipeline, local Docker Compose stack, and Render deployment blueprints, established in Week 1.

---

## 3. Balancing Notes & Collaboration

- **Person 1** carries the scientific risk and interfaces with bioprocess advisors. All formulas require dual sign-off.
- **Person 3** owns data ingestion, vessel compatibility, and assessment orchestration.
- **Person 2 and Person 4** collaborate closely on DevOps, API architecture, database integrity, and security hardening.
- **Person 4** guarantees product quality, auditability, automated database backups, and client-ready reporting with disclaimers.

---

## 4. Review Gates

- **Scientific Requirements & Formulas:** Lead = Person 1; Reviewer = external bioprocess advisor + Person 2.
- **Database Schema, API & Tenancy:** Lead = Person 2; Reviewers = Person 3 + Person 4.
- **Readiness Engines & Ingestion:** Lead = Person 3; Reviewers = Person 1 + Person 2.
- **Reporting, Infrastructure & CI:** Lead = Person 4; Reviewers = Person 2 + Person 3.
