# ScaleBridge Bio — Technical Documentation Repository

> **Bioprocess scale-up & intelligence platform.**
> A vendor-agnostic, process-aware decision-support layer that compares lab-scale process data with target-vessel capabilities, surfaces scale-up trade-offs, and creates an evidence-linked validation plan.
> — *ScaleBridge Bio Startup Blueprint, 16 Nov 2026 (Confidential Working Draft)*

This repository is the **single technical reference** for building the ScaleBridge Bio MVP. It is written for human developers and AI coding agents. It contains **no application code**.

---

## 1. Source of truth and labelling convention

The primary source is `ScaleBridge_Bio_Startup_Blueprint.pdf` (17 pages, "the Blueprint"). Page references are written `[BP p.N]`. Blueprint citations `[S1]…[S14]` are preserved as given.

Every requirement or decision in these documents is labelled:

| Label | Meaning | Who may change it |
|---|---|---|
| **CONFIRMED** | Explicitly stated or directly supported by the Blueprint. | Founders only. |
| **PROPOSED** | A technical recommendation made by the documentation author to make the Blueprint implementable. Not in the Blueprint. | Owning lead (see [20_TEAM_RESPONSIBILITIES.md](docs/20_TEAM_RESPONSIBILITIES.md)); scientific items also need Person 1 + advisor. |
| **OPEN QUESTION** | Requires founder or domain-expert confirmation. Tracked as `OQ-NNN` in [22_OPEN_QUESTIONS.md](docs/22_OPEN_QUESTIONS.md). | Resolved by named owner; resolution recorded in doc 22. |

> [!IMPORTANT]
> No scientific threshold, correlation or numeric heuristic is invented in these documents. Where the Blueprint names a check but gives no threshold, the threshold is a **configuration value owned by the scientific lead** and the rule returns `not_configured` until it is set. See [12_RISK_ENGINE.md](docs/12_RISK_ENGINE.md).

---

## 2. What we are building (one paragraph)

A **web-based scale-up readiness and technology-transfer decision-support workspace** for microbial batch / fed-batch fermentation (initial wedge: aerobic microbial fermentation for industrial enzymes and fermentation-derived ingredients). A bioprocess scientist creates a **Process Passport**, imports batch data (CSV/XLSX), describes a lab vessel and a target vessel, selects a scale-up scenario, and receives side-by-side engineering calculations (OTR, P/V, tip speed, Reynolds number, vvm, kLa where supported), an explainable **risk register**, an **equipment compatibility** assessment, a **validation plan**, and a PDF **Transfer Report**. The system is **not** a controller, **not** a validated digital twin, and **never** turns missing information into a confident prediction — *"Insufficient evidence" is a valid and valuable output* `[BP p.4]` (CONFIRMED).

---

## 3. Repository map

```
ScaleBridge-Bio/
├── .github/
│   └── workflows/
│       ├── ci.yml                     ← Automated test & typecheck pipeline
│       └── deploy.yml                 ← Container build & release workflow
├── docs/                              ← Architecture & scientific specs (01..23)
├── ai-context/                        ← Agent guidelines & coding rules
├── sample-data/
│   └── synthetic/                     ← Clearly labeled reference test data
├── backend/                           ← Python 3.12 / FastAPI modular monolith
│   ├── scalebridge_science/           ← Pure, deterministic scientific engine (zero I/O)
│   ├── app/                           ← Web services, DB persistence, RBAC, endpoints
│   ├── tests/                         ← API and integration test suite
│   ├── Dockerfile                     ← Production container configuration
│   ├── pyproject.toml                 ← Modern packaging & dependency definitions
│   ├── requirements.txt               ← Frozen dependencies for PaaS/Docker
│   └── .env.example                   ← Documented environment variables
├── frontend/                          ← TypeScript / Next.js 14 App Router
│   ├── src/                           ← React components, pages, and API client
│   ├── Dockerfile                     ← Production container configuration
│   ├── package.json                   ← Frontend dependencies and scripts
│   ├── vercel.json                    ← Vercel deployment specification
│   └── .env.example                   ← Frontend environment variables
├── docker-compose.yml                 ← Local multi-container development stack
├── render.yaml                        ← Render PaaS blueprint for Web + PostgreSQL
└── README.md                          ← You are here
```

## 4. Reading order

| Reader | Read in this order |
|---|---|
| **AI coding agent** | `ai-context/PROJECT_CONTEXT.md` → `ai-context/ARCHITECTURE_RULES.md` → `ai-context/CODING_RULES.md` → `ai-context/DEVELOPMENT_INSTRUCTIONS.md` → the doc(s) for the module being built |
| Backend developer | 05 → 06 → 07 → 08 → 09 → 17 → 21 |
| Scientific / modelling developer | 10 → 11 → 12 → 13 → 14 → 18 |
| Frontend developer | 03 → 15 → 16 → 08 |
| Founders / advisors | 01 → 02 → 04 → 19 → 20 → 22 → 23 |

## 5. Canonical glossary (use these exact terms in code and UI)

| Term | Definition | Code identifier |
|---|---|---|
| **Process Passport** | Structured, versioned record of process parameters, batch data, vessel characteristics, material context and provenance `[BP p.4]`. | `project`, `passport_version` |
| **Batch / Run** | One fermentation run with metadata and time-series measurements. | `batch` |
| **Measurement** | One time-stamped value of one variable with unit, source and quality flag. | `measurement` |
| **Sample / Assay** | Offline sample result (biomass, substrate, titre…). | `sample` |
| **Vessel Profile** | Versioned geometry + capability envelope of a bioreactor. | `vessel`, `vessel_version` |
| **Scenario** | A user-configured comparison: source batch(es) + source vessel → target vessel + target volume + selected scale-up criteria + constraints. | `scenario` |
| **Assessment** | An immutable, reproducible execution of a Scenario producing calculations, risk flags, compatibility checks and validation tasks. | `assessment` |
| **Scale-up Risk Engine** | Rule-based comparison of engineering constraints; flags conflicts and unevaluable criteria `[BP p.4]`. | `readiness.risk` |
| **Equipment Compatibility Engine** | Checks whether a target vessel's documented capability envelope supports the process requirements `[BP p.4]`. | `readiness.compatibility` |
| **Validation Planner** | Converts gaps into a prioritized list of measurements, experiments and expert reviews `[BP p.4]`. | `readiness.validation` |
| **Readiness Engine** | Umbrella component containing the three engines above `[BP p.10]`. | `readiness` |
| **Transfer Report** | PDF process-transfer passport: summary, vessel comparison, calculations, flags, missing data, validation plan `[BP p.5]`. | `report` |
| **Provenance** | Where a value came from: `sensor`, `manual_entry`, `lab_assay`, `vendor_datasheet`, `published_correlation`, `user_assumption` `[BP p.6]` (+ `calculated`, PROPOSED). | `provenance` |
| **Value nature** | `measured`, `estimated`, `assumed`, `calculated` — measured and estimated must never be confused `[BP p.6]`. | `value_nature` |
| **Insufficient evidence** | First-class outcome when inputs are missing or unvalidated. | `insufficient_evidence` |

## 6. Non-negotiable product principles (CONFIRMED)

1. Decision support, **not** an autonomous process controller; no writing setpoints to live controllers `[BP p.4, p.5, p.10]`.
2. Show inputs, units, assumptions, model limits and evidence behind every conclusion `[BP p.4]`.
3. Missing information never becomes a confident prediction `[BP p.4]`.
4. Deterministic, unit-tested calculations first; ML only after sufficient real, governed data `[BP p.6, p.10]`.
5. No claim that constant kLa, P/V, tip speed and mixing time can be preserved simultaneously `[BP p.6]`.
6. No claims of novelty ("first"), validated digital twin, guaranteed yield, GMP or 21 CFR Part 11 compliance `[BP p.2, p.5, p.15]`.
7. Synthetic/demo data must be clearly labelled `[BP p.5]`.
