# 03 — Product Requirements

**Purpose:** Enumerate testable functional (FR) and non-functional (NFR) requirements. Each has an ID referenced by other docs, tests and backlog items.
**Related:** [04_MVP_SCOPE.md](04_MVP_SCOPE.md) · [08_API_SPECIFICATION.md](08_API_SPECIFICATION.md) · [15_UI_UX_SPECIFICATION.md](15_UI_UX_SPECIFICATION.md) · [16_USER_WORKFLOWS.md](16_USER_WORKFLOWS.md) · [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md)

Priority: **M** = MVP must; **S** = MVP should (cut if time-boxed); **L** = later (post-MVP, not to be built without approval).

---

## 1. Identity, organizations, access (module: `identity`)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-ID-01 | Users authenticate with email + password. | M | PROPOSED (Blueprint requires "login" `[BP p.12]` and authentication `[BP p.10]`; method unspecified) |
| FR-ID-02 | Every tenant record belongs to exactly one organization; users only see data of organizations they are members of. | M | CONFIRMED "organization separation / isolation" `[BP p.10]` |
| FR-ID-03 | Role-based access with roles `org_admin`, `scientist`, `reviewer`, `viewer` (permissions matrix in [17](17_SECURITY_AND_PRIVACY.md) §4). | M | CONFIRMED RBAC `[BP p.10]`; role names PROPOSED (**OQ-021**) |
| FR-ID-04 | Org admins invite users by email; no public self-signup in MVP. | M | PROPOSED (**OQ-030**) |
| FR-ID-05 | SSO (SAML/OIDC). | L | CONFIRMED as enterprise tier `[BP p.8]` |

## 2. Process Passport (module: `projects`)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-PP-01 | Create a project with name, product family, organism/strain metadata, process type (`batch`, `fed_batch`, `other`), owner. | M | CONFIRMED `[BP p.4, p.11]` |
| FR-PP-02 | Passport is **versioned**: each save of process context creates an immutable `passport_version` (recipe version, process parameters with units, medium/material context, feed strategy, change note). | M | CONFIRMED "versioned" `[BP p.4]` |
| FR-PP-03 | System generates a **data checklist** for the project showing which inputs required by downstream calculations are present, missing, estimated or assumed. | M | CONFIRMED "data checklist" `[BP p.4]` |
| FR-PP-04 | Project can be flagged `is_synthetic_demo`; the flag propagates to every view and report. | M | CONFIRMED labelling of synthetic data `[BP p.5]` |
| FR-PP-05 | Passport version diff view. | S | PROPOSED (12-month roadmap mentions passport versioning months 7–9 `[BP p.16]`) |

## 3. Data ingestion (module: `ingestion`) — detail in [09](09_DATA_INGESTION.md)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-DI-01 | Upload CSV and XLSX files; raw file stored unchanged with SHA-256 hash. | M | CONFIRMED `[BP p.5, p.11]` |
| FR-DI-02 | Column mapping UI: map source columns to canonical variables, timestamp column, and units; mapping saved and reusable. | M | CONFIRMED `[BP p.5]` |
| FR-DI-03 | Unit normalization via Pint; store original value+unit and normalized value+unit; record every conversion. | M | CONFIRMED `[BP p.6, p.11]` |
| FR-DI-04 | Data-quality checks: timestamp order, gaps, duplicates, impossible values, out-of-range sensor readings, missing values. | M | CONFIRMED `[BP p.11]` |
| FR-DI-05 | Data-quality summary shown before import is committed. | M | CONFIRMED acceptance test `[BP p.5]` |
| FR-DI-06 | Batch metadata capture: run ID, start/end, scale, vessel, recipe/passport version, operator, notes. | M | CONFIRMED `[BP p.11]` |
| FR-DI-07 | Offline samples/assays (biomass, substrate, titre) importable as separate sheet/file. | M | CONFIRMED entity `[BP p.11]` |
| FR-DI-08 | Raw values never silently overwritten; corrections are new records with audit trail. | M | CONFIRMED `[BP p.11]` |
| FR-DI-09 | Read-only equipment integrations (OPC UA, Modbus, MQTT). | L | CONFIRMED later `[BP p.10, p.16]` |

## 4. Process dashboard (module: `batches` UI)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-DB-01 | Trend plots for pH, DO, temperature, RPM, airflow, feed, biomass/OD, product titre where available. | M | CONFIRMED `[BP p.5]` |
| FR-DB-02 | Overlay/compare at least two batches (by elapsed time). | M | CONFIRMED `[BP p.5]` |
| FR-DB-03 | Quality-flagged points visually distinguished; missing data shown as gaps, not interpolated. | M | PROPOSED, implements "make missing data visible" `[BP p.11]` |

## 5. Vessel profiles (module: `vessels`) — detail in [13](13_EQUIPMENT_COMPATIBILITY.md)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-VS-01 | Create/edit vessel profiles: working volume (min/max/nominal), dimensions, impeller type/diameter/count, motor limits, agitation range, sparger, gas flow range, cooling/heating capability, instrumentation & controls. | M | CONFIRMED `[BP p.5, p.11]` |
| FR-VS-02 | Every vessel parameter carries unit and provenance (`vendor_datasheet`, `manual_entry`, `user_assumption`, …) and optional source reference. | M | CONFIRMED provenance `[BP p.6, p.15]` |
| FR-VS-03 | Vessel profiles are versioned; assessments reference a specific version. | M | CONFIRMED `[BP p.11]` |
| FR-VS-04 | Missing-specification warnings per vessel relative to parameters required by calculations. | M | CONFIRMED `[BP p.4]` |
| FR-VS-05 | Side-by-side comparison of two vessel profiles. | M | CONFIRMED `[BP p.5]` |
| FR-VS-06 | Shared/verified facility vessel library across organizations. | L | CONFIRMED later "facility / ecosystem tools" `[BP p.8]` |

## 6. Scenarios & scale-up calculations (modules: `scenarios`, `science`) — detail in [10](10_SCIENTIFIC_ENGINE.md), [11](11_SCALE_UP_CALCULATIONS.md)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-SC-01 | Create a scenario: source batch(es), source vessel version, target vessel version, target working volume, selected scale-up criteria (one marked primary), process constraints, explicit assumptions. | M | CONFIRMED `[BP p.4, p.11]` |
| FR-SC-02 | Compute for source and target: P/V, tip speed, Reynolds number, vvm, OTR and kLa **where data supports them**. | M | CONFIRMED `[BP p.5–6]` |
| FR-SC-03 | Each result shows equation, units, inputs (with provenance and value nature) and assumptions. | M | CONFIRMED acceptance test `[BP p.5]` |
| FR-SC-04 | For each selected criterion, compute the target operating point that preserves it and show how all other descriptors change (trade-off table). | M | CONFIRMED "criterion trade-offs" `[BP p.4, p.6]`; derivations PROPOSED ([11](11_SCALE_UP_CALCULATIONS.md) §8) |
| FR-SC-05 | Calculations lacking inputs return `insufficient_evidence` naming the missing inputs; never default silently. | M | CONFIRMED `[BP p.4, p.11]` |
| FR-SC-06 | Running a scenario creates an immutable **Assessment** recording engine, formula and rule-registry versions and an input snapshot. | M | CONFIRMED reproducibility `[BP p.11]` |
| FR-SC-07 | Numerical optimization (CasADi/GEKKO). | L | CONFIRMED optional later `[BP p.10]` |
| FR-SC-08 | ML predictions (scikit-learn, XGBoost, MLflow). | L | CONFIRMED later `[BP p.10]` |

## 7. Readiness (module: `readiness`) — detail in [12](12_RISK_ENGINE.md), [13](13_EQUIPMENT_COMPATIBILITY.md), [14](14_VALIDATION_PLANNER.md)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-RK-01 | Rule-based risk flags for oxygen transfer, mixing, thermal capability, missing data and equipment limits. | M | CONFIRMED `[BP p.5]` |
| FR-RK-02 | Every flag links to specific input(s), the rule (ID+version) and the evidence gap. | M | CONFIRMED acceptance test `[BP p.5]` |
| FR-RK-03 | Each flag has severity and an evidence/confidence label. | M | CONFIRMED "confidence", "uncertainty labels" `[BP p.4, p.10]`; scale PROPOSED |
| FR-EC-01 | Equipment compatibility checks target vessel envelope vs required operating point; outcomes `compatible`/`incompatible`/`cannot_evaluate`. | M | CONFIRMED `[BP p.4]`; outcomes PROPOSED |
| FR-VP-01 | Validation Planner generates prioritized tasks (measurement, experiment, expert review, data request) from flags and gaps. | M | CONFIRMED `[BP p.4]`; `data_request` type PROPOSED |
| FR-VP-02 | Users can update task status (`open`, `in_progress`, `done`, `waived` with mandatory reason). | S | PROPOSED |
| FR-RV-01 | A `reviewer` can record a human review decision on an assessment (approved for discussion / changes requested) with comment. | M | CONFIRMED "human sign-off" mitigation `[BP p.15]`; semantics OPEN (**OQ-023**) |

## 8. Transfer Report (module: `reports`)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-RP-01 | Generate PDF with: process summary, vessel comparison, calculations (with equations/inputs/assumptions), risk flags, missing data, compatibility, validation plan, limitations statement, review status. | M | CONFIRMED `[BP p.5]`; limitations/review sections PROPOSED |
| FR-RP-02 | Report is versioned, stored in object storage with hash, and references exactly one assessment. | M | CONFIRMED versioning `[BP p.11]` |
| FR-RP-03 | Synthetic-data watermark on every page when any input is synthetic. | M | CONFIRMED labelling `[BP p.5]` |
| FR-RP-04 | Report includes standard disclaimer: decision support, not an engineering design package or validated prediction. | M | CONFIRMED `[BP p.17]` wording basis |

## 9. Audit (module: `audit`)

| ID | Requirement | Pri | Label |
|---|---|---|---|
| FR-AU-01 | Append-only audit events for create/update/delete/import/assess/report/review/login and permission changes. | M | CONFIRMED audit logging `[BP p.10–11]` |
| FR-AU-02 | Org admins can view and filter audit events. | S | PROPOSED |

---

## 10. Non-functional requirements

| ID | Requirement | Label |
|---|---|---|
| NFR-01 Traceability | 100% of supported calculations display inputs, units, assumptions. | CONFIRMED metric `[BP p.14]` |
| NFR-02 Correctness | 100% pass on agreed calculation unit-test set; no unresolved critical errors. | CONFIRMED `[BP p.14]` |
| NFR-03 Import success | ≥90% of agreed test files import without manual rework. | CONFIRMED `[BP p.14]` |
| NFR-04 Reproducibility | Re-running an assessment from its snapshot with the same engine version produces bit-identical numeric outputs. | PROPOSED, implements `[BP p.11]` |
| NFR-05 Security | Org isolation, RBAC, TLS in transit, encryption at rest, backups, audit logging, customer-controlled retention. | CONFIRMED `[BP p.10]` |
| NFR-06 Determinism | Scientific engine is pure and deterministic (no network, DB, randomness, or clock). | CONFIRMED "deterministic" `[BP p.6]` |
| NFR-07 Performance | Import of a 100k-row file < 30 s; assessment < 5 s; report < 30 s on reference hardware. | PROPOSED |
| NFR-08 Availability | Pilot-grade (no SLA in MVP); daily backups, tested restore. | PROPOSED |
| NFR-09 Browser | Latest Chrome, Edge, Firefox; desktop ≥1280 px. Mobile not supported. | PROPOSED |
| NFR-10 Language | English UI. | PROPOSED (**OQ-029**) |
| NFR-11 Deployability | Docker-based; cloud or on-premise path. | CONFIRMED `[BP p.10]` |
| NFR-12 Honesty | No UI text, report text or API field may describe an estimate as a measurement or claim validation that has not occurred. | CONFIRMED `[BP p.6, p.15]` |

## 11. Acceptance criteria
Each FR marked **M** has at least one automated test or documented manual test case in [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md); backlog items reference FR IDs.
