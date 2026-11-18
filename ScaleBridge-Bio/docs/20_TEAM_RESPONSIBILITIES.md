# 20 — Team Responsibilities

**Purpose:** Document role ownership, review gates and operating rhythm `[BP p.12–13]`.
**Related:** [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [19_DEVELOPMENT_ROADMAP.md](19_DEVELOPMENT_ROADMAP.md)

---

## 1. Four-person founding team (CONFIRMED `[BP p.13]`)

| Role | Primary ownership | Key deliverables |
|---|---|---|
| 1. Bioprocess / scientific lead | Fermentation domain, process workflow, scale-up criteria, vessel specs, scientific review | Requirements; formula & assumption register; validated sample data; scientific review; lab/mentor relationships |
| 2. Computational / modelling lead | Python calculation engine, data analysis, scenario logic, future predictive modelling | `scalebridge_science` library; scale-up engine; rule logic; evaluation tests; model versioning |
| 3. Backend / infrastructure lead | APIs, database, file ingestion, identity, storage, deployment, security | FastAPI services; schema; upload pipeline; authentication; audit trail; deployment |
| 4. Frontend / product / business lead | UX, dashboards, customer discovery, competitor research, pitch, incubation materials | Next.js interface; demo flow; interview notes; pricing tests; pitch deck; incubation proposal |

## 2. Review gates (CONFIRMED `[BP p.13]`)
- **Scientific requirements & validation:** Lead = Person 1; Reviewers = Person 2 + external bioprocess advisor.
- **Scientific calculation engine (`scalebridge_science`):** Lead = Person 2; Reviewer = Person 1 (every formula change requires both).
- **Backend, database & deployment:** Lead = Person 3; Reviewers = Person 2 + Person 4.
- **Frontend & UX:** Lead = Person 4; Reviewers = Person 3 + Person 1.
