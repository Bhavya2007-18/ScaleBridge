# 04 — MVP Scope

**Purpose:** Define exactly what the MVP contains, what it excludes, and how each part is accepted. This document wins any scope dispute.
**Related:** [03_PRODUCT_REQUIREMENTS.md](03_PRODUCT_REQUIREMENTS.md) · [19_DEVELOPMENT_ROADMAP.md](19_DEVELOPMENT_ROADMAP.md) · [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md)

---

## 1. MVP goal (CONFIRMED `[BP p.5]`)
> Demonstrate one end-to-end use case: compare a documented laboratory fermentation process with a proposed larger vessel and produce an evidence-linked readiness report.

**Decision gate (CONFIRMED `[BP p.16]`):** one process family, one customer workflow, one target vessel comparison, one report a bioprocess engineer is willing to review. Do **not** build "AI for all bioprocessing".

## 2. In scope — MVP modules and acceptance tests (CONFIRMED `[BP p.5]`)

| MVP module | First-version capability | Acceptance test (Blueprint) | FR IDs |
|---|---|---|---|
| Data ingestion | CSV/XLSX upload; column mapping; timestamps; units; missing values; batch metadata | A user can import one complete batch and see a data-quality summary | FR-DI-01…08 |
| Process dashboard | Trends for pH, DO, temperature, RPM, airflow, feed, biomass/OD, product titre where available | A user can inspect and compare at least two batches | FR-DB-01…03 |
| Vessel profiles | Working volume, dimensions, impeller diameter/type, motor limits, gas flow, available instrumentation | Two vessels can be saved and compared | FR-VS-01…05 |
| Scale-up calculations | kLa/OTR where data supports, P/V, tip speed, Reynolds number, gas-flow descriptors | Each result shows equation, units, inputs and assumptions | FR-SC-01…06 |
| Risk assessment | Rule-based warnings: oxygen transfer, mixing, thermal capability, missing data, equipment limits | Every flag links to a specific input, rule and evidence gap | FR-RK-*, FR-EC-01 |
| Transfer report | PDF: process summary, vessel comparison, calculations, flags, missing data, validation plan | Report can be generated and reviewed by a domain expert | FR-RP-*, FR-VP-01 |

Supporting MVP capabilities (required to make the above work):

| Capability | Label |
|---|---|
| Login, organizations, RBAC, audit log | CONFIRMED `[BP p.10, p.12]` |
| Process Passport with versioning and data checklist | CONFIRMED `[BP p.4, p.12]` |
| Validation Planner (rule-generated tasks) | CONFIRMED `[BP p.4, p.12 wks 8–9]` |
| Equipment Compatibility Engine | CONFIRMED `[BP p.12 wks 8–9]` |
| Reviewer sign-off record | CONFIRMED mitigation `[BP p.15]` |
| Synthetic-data labelling | CONFIRMED `[BP p.5]` |

## 3. Explicitly out of scope (CONFIRMED `[BP p.5]` unless marked)

| Excluded | Reason / note |
|---|---|
| Autonomous control of live bioreactors or writing setpoints | CONFIRMED |
| Universal "AI optimal recipe" recommendations | CONFIRMED |
| Fully validated digital twin / guaranteed commercial-yield prediction | CONFIRMED |
| GMP production execution, electronic batch records, 21 CFR Part 11 claims | CONFIRMED |
| Marketplace with unverified third-party facility availability claims | CONFIRMED |
| Live equipment integrations (OPC UA, Modbus TCP/RTU, MQTT) | CONFIRMED later (months 7–9, read-only) `[BP p.10, p.16]` |
| ML models (scikit-learn, XGBoost, MLflow) | CONFIRMED later `[BP p.10]` |
| Numerical optimization (CasADi/GEKKO) | CONFIRMED optional later `[BP p.10]` |
| SSO, custom connectors, private deployment packaging | CONFIRMED enterprise tier `[BP p.8]` |
| Billing / subscription management | PROPOSED exclusion (sales are manual during pilots) |
| Generic chatbot / LLM summarization of data | CONFIRMED "what not to build" `[BP p.9]` |
| kLa correlations not approved by scientific lead | PROPOSED exclusion pending **OQ-011** |
| Mixing-time, heat-balance and OUR-from-off-gas *calculations* | PROPOSED exclusion: Blueprint names the evidence but gives no equations; MVP accepts these as user-supplied values only (**OQ-010, OQ-015, OQ-016**) |
| Mammalian cell culture, anaerobic, continuous processes | PROPOSED exclusion (wedge is aerobic microbial batch/fed-batch) |
| Multi-site / shared facility vessel library | CONFIRMED later `[BP p.8]` |
| Mobile UI, localization | PROPOSED exclusion |
| Real-time streaming / TimescaleDB | PROPOSED: start with plain PostgreSQL (TimescaleDB "optional" `[BP p.10]`, **OQ-026**) |

> [!WARNING]
> AI coding agents must not implement any item in §3 without written approval recorded in [22_OPEN_QUESTIONS.md](22_OPEN_QUESTIONS.md).

## 4. MVP data strategy

| Phase | Data | Label |
|---|---|---|
| Hackathon demo | Clearly labelled **synthetic or published** data: upload, vessel comparison, risk explanation, report generation | CONFIRMED `[BP p.5]` |
| Incubation | Replace demo with a **real partner dataset** and **expert-reviewed calculations** | CONFIRMED `[BP p.5]` |
| Critical path | Secure one real fermentation dataset and one domain expert early | CONFIRMED `[BP p.12]` |

Repository convention (PROPOSED): `sample-data/synthetic/` (generated, documented generator parameters) and `sample-data/published/` (with citation + licence). Never commit partner data. See **OQ-002, OQ-004**.

## 5. MVP reference scenario (PROPOSED shape; values come from dataset, OQ-001/OQ-004)
- 1 project, 1 passport version, 2 lab batches (same vessel) for comparison.
- Source vessel: lab benchtop (~2 L working volume class, per Blueprint example `[BP p.3]`).
- Target vessel: pilot (e.g., 20 L or 200 L class `[BP p.3]`).
- Scenario criteria: constant P/V (primary), constant tip speed, constant vvm; constant kLa evaluated only if target kLa evidence exists.
- Expected output: calculations table, trade-off table, ≥1 flag per category or explicit `not_triggered`/`insufficient_evidence`, compatibility matrix, validation plan, PDF report.

## 6. MVP definition of done
1. All six Blueprint acceptance tests in §2 pass on the reference dataset.
2. Metrics in [18](18_TESTING_AND_VALIDATION.md) §6 meet targets (≥90% import, 100% calculation tests, 100% traceability).
3. A domain expert has reviewed the formula register and one generated report; findings logged (Week 10–11 exit condition: "reviewed prototype with documented limitations" `[BP p.12]`).
4. At least 3 supervised external users complete the workflow without founder intervention `[BP p.14]`.
5. No item from §3 is present in the codebase.
