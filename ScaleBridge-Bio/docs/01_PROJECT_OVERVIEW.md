# 01 — Project Overview

**Purpose:** Establish what ScaleBridge Bio is, who it serves, how it is positioned, and the boundaries every other document inherits.
**Related:** [02_PROBLEM_AND_SOLUTION.md](02_PROBLEM_AND_SOLUTION.md) · [03_PRODUCT_REQUIREMENTS.md](03_PRODUCT_REQUIREMENTS.md) · [04_MVP_SCOPE.md](04_MVP_SCOPE.md) · [19_DEVELOPMENT_ROADMAP.md](19_DEVELOPMENT_ROADMAP.md)

---

## 1. Identity

| Item | Value | Label |
|---|---|---|
| Name | ScaleBridge Bio | CONFIRMED |
| Category | Biomanufacturing / deep tech; B2B software | CONFIRMED `[BP p.1–2]` |
| Tagline | Bioprocess scale-up & intelligence platform | CONFIRMED `[BP p.1]` |
| Mission | Move fermentation processes from laboratory development to pilot and commercial manufacturing | CONFIRMED `[BP p.1]` |
| Document status of source | Confidential working draft, prepared 16 Nov 2026, for hackathon-to-incubation planning | CONFIRMED `[BP p.1, p.17]` |
| Initial geography | India, with global expansion potential | CONFIRMED `[BP p.1]` |

### 1.1 Startup thesis (CONFIRMED, verbatim `[BP p.1]`)
> A vendor-agnostic, process-aware decision-support layer that compares lab-scale process data with target-vessel capabilities, surfaces scale-up trade-offs, and creates an evidence-linked validation plan.

### 1.2 The four-stage flow (CONFIRMED `[BP p.1]`)

```mermaid
flowchart LR
  A["01 LAB DATA"] --> B["02 ENGINEERING"] --> C["03 RISK REVIEW"] --> D["04 TRANSFER"]
```

| Stage | Meaning in the product | Implementing module |
|---|---|---|
| 01 Lab data | Process Passport + batch data import | Ingestion, Projects ([09](09_DATA_INGESTION.md)) |
| 02 Engineering | Vessel profiles + scale-up calculations | Scientific Engine ([10](10_SCIENTIFIC_ENGINE.md), [11](11_SCALE_UP_CALCULATIONS.md)) |
| 03 Risk review | Risk register, compatibility, missing evidence | Readiness Engine ([12](12_RISK_ENGINE.md), [13](13_EQUIPMENT_COMPATIBILITY.md)) |
| 04 Transfer | Validation plan + Transfer Report | Validation Planner, Reports ([14](14_VALIDATION_PLANNER.md)) |

## 2. Product snapshot (CONFIRMED `[BP p.2]`)

| Dimension | Initial position |
|---|---|
| Product | Web-based scale-up readiness and technology-transfer decision support. |
| Primary user | Bioprocess scientist or process-development engineer. |
| Economic buyer | CTO, R&D director, head of process development or manufacturing director. |
| Initial process scope | Microbial batch / fed-batch fermentation; narrow to one process family during discovery. |
| Core workflow | Upload batch data → describe vessels → compare criteria → review risks → plan validation. |
| Business model | Annual B2B subscription + paid technical assessment + enterprise integration. |
| First proof point | A real or properly documented lab dataset compared with a second vessel configuration and reviewed by a bioprocess expert. |

### 2.1 Recommended wedge (CONFIRMED `[BP p.2, p.16]`)
Aerobic microbial fermentation for **industrial enzymes** and **fermentation-derived / bio-based ingredients**. Sell first to early-stage biotech manufacturers, process-development teams and specialist CDMOs moving from bench to pilot runs.

> OPEN QUESTION **OQ-001**: Which single process family (organism class, product, batch vs fed-batch) is the MVP reference process? The Blueprint says to narrow during discovery (weeks 1–2).

## 3. Users and stakeholders (CONFIRMED `[BP p.7]`)

| Role | Cares about | Product implication |
|---|---|---|
| Daily user — bioprocess scientist / engineer | Usable data, correct calculations, transparent assumptions, less manual report prep | Import wizard, equation cards, auto report |
| Technical champion — CTO / process-development lead | Faster decisions, lower uncertainty, defensible scale-up plan | Risk register, validation plan, sign-off |
| Economic buyer — R&D / manufacturing director | Less engineering rework, better facility utilization, transfer consistency | Report quality, repeatability |
| Influencer — pilot facility / CDMO technical lead | Complete, comparable process data; clear equipment requirements and missing evidence | Transfer Report, compatibility matrix |

### 3.1 Customer segments (CONFIRMED `[BP p.7]`)

| Segment | Buying trigger | Priority |
|---|---|---|
| Industrial enzyme manufacturers | Repeatability; move process between vessels/sites; reduce rework | High |
| Precision fermentation / alt-protein startups | Scale-up feasibility & pilot-facility fit before committing capital | High |
| Probiotic / microbial ingredient manufacturers | Batch comparability; transfer process knowledge | High |
| CDMOs / contract fermentation facilities | Evaluate client processes; document equipment suitability & handoffs | High |
| Biofoundries / research institutions | Standardize experiment records; industry-facing transfer packages | Partner channel |

## 4. Signature modules (CONFIRMED `[BP p.4]`)

1. **Process Passport** — structured, versioned record of process parameters, batch data, vessel characteristics, material context and provenance.
2. **Scale-up Risk Engine** — compares engineering constraints; highlights where criteria conflict or cannot be evaluated due to missing data.
3. **Equipment Compatibility Engine** — checks whether a target vessel's documented capability envelope can support the process requirements.
4. **Validation Planner** — converts gaps into a prioritized list of measurements, experiments and expert reviews needed before a pilot run.

## 5. Market positioning

### 5.1 Positioning rules (CONFIRMED `[BP p.2, p.9]`)
- Do **not** claim ScaleBridge is the first bioprocess dashboard, digital twin or scale-up tool.
- Differentiation hypothesis (not proven): the *combination* of (1) process passport data, (2) vessel-specific engineering capability, (3) explainable criterion trade-offs and uncertainty, (4) a validation plan for a target pilot facility.
- The product helps teams decide **what can be transferred, what is unknown, and what evidence is still needed**.

### 5.2 Competitive landscape (CONFIRMED, vendor-stated capabilities `[BP p.9]`)

| Provider / product | Publicly described capabilities | Implication |
|---|---|---|
| Eppendorf DASware / BioNsight [S7] | SCADA, monitoring, control, cloud monitoring & analysis | Don't compete on basic monitoring or native control |
| Getinge / Lucullus PIMS [S8] | Planning, data integration, DoE, analysis, reporting, multi-site comparison | Don't pitch a generic data warehouse / batch dashboard |
| Benchling Bioprocess [S9] | Process development, recipe design, experiment planning, batch execution, visualization, tech-transfer | Acknowledge tech-transfer exists in category |
| BioRaptor [S10] | Cross-run analysis, contextualization, reporting, dashboards, RCA, monitoring | Differentiate beyond batch analytics |
| Janussphere [S11] | AI digital twins, analytics, media optimization, fault detection, DOE | Don't claim digital twins/predictive optimization as novel |

### 5.3 What not to build (CONFIRMED `[BP p.9]`)
- A generic bioreactor dashboard charting pH, DO and temperature (the MVP dashboard exists only to serve the scale-up workflow).
- A generic AI chatbot summarizing fermentation data without validated calculations.
- A generic digital twin without a process-specific model and validation dataset.
- A broad equipment directory without verified specifications or availability.

## 6. Business model summary (CONFIRMED `[BP p.8]`)

| Revenue stream | When |
|---|---|
| Paid scale-up assessment (expert-supported, fixed scope) | Early — paid discovery/pilot |
| Annual SaaS subscription | After MVP pilot proves repeat use |
| Enterprise integration (instrument connectors, private deployment, SSO) | After PMF signals |
| Facility / ecosystem tools | Later, after trust and verified data |

Pricing hypotheses (₹3–6 lakh startup; ₹6–15 lakh SME; ₹15–30 lakh+ CDMO; ₹1–3 lakh per pilot assessment) are **hypotheses for willingness-to-pay interviews, not benchmarks**. Illustrative scenario: 100 accounts × ₹6 lakh = ₹6 crore ARR — **not a forecast**.

Market context (ecosystem indicators, **not TAM**): India bioeconomy US\$195.3 B (2025), BioIndustrial US\$90.2 B (46%) [S1]; ~774,170 kL fermentation-relevant capacity across 29 states [S2].

**Software implication (PROPOSED):** The MVP has no billing, subscription or licensing code. Paid assessments are delivered as a service using the same product. See [04_MVP_SCOPE.md](04_MVP_SCOPE.md).

## 7. Ecosystem and partnership context (CONFIRMED `[BP p.3, p.15]`)
BioE3 policy (high-performance biomanufacturing priority) [S3, S4, S14]; DBT Bio-based Chemicals & Enzymes programme [S5]; DBT/BIRAC Biofoundries & Biomanufacturing Hubs user-access policy (1 Aug 2025) [S6]; BIRAC/BioNEST incubators; university chemical/biochemical engineering departments for scientific review and data/equipment access.

## 8. Success definition for the MVP (CONFIRMED `[BP p.14]`)
See [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md) §6 for metrics. Go/No-Go: proceed beyond MVP only if users confirm the problem is frequent and costly, the product adds value beyond existing tools, and at least one organization will share data or co-design a pilot.

## 9. Acceptance criteria for this document
- Every downstream doc uses the glossary in [README.md](../README.md) §5.
- No downstream doc contradicts §5.1 positioning rules or §5.3 "what not to build".
