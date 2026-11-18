# 18 — Testing and Validation

**Purpose:** Define the five validation layers from `[BP p.11]`, MVP success metrics from `[BP p.14]`, and automated test requirements.
**Related:** [04_MVP_SCOPE.md](04_MVP_SCOPE.md) · [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md)

---

## 1. Five validation layers (CONFIRMED `[BP p.11]`)

| Layer | How to validate | Automated / manual artifact |
|---|---|---|
| 1. Software correctness | Unit tests with known values; regression tests; dimensional analysis; error handling | `pytest` suite (`scalebridge_science/tests`, `backend/tests`), `vitest` frontend suite |
| 2. Engineering correctness | Independent calculation review by a bioprocess engineer; comparison with trusted engineering references | Formula register review sign-off + independent spreadsheet/script verification of T1–T14 |
| 3. Equipment realism | Check profiles against manufacturer specifications and measurements from partner facilities | Seeded reference vessel templates with provenance |
| 4. Process relevance | Compare outputs with actual batches and pilot observations; document where models do not generalize | Limitations section on every assessment and PDF report |
| 5. User value | Observe scientists using the workflow; measure reporting time, missing-data detection and usefulness | Supervised usability protocol (≥3 external users `[BP p.14]`) |

## 2. Automated test suites

### 2.1 Scientific engine (`scalebridge_science/tests/`)
- **Known-value tests:** T1–T14 from [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md) §9 (`rel = 1e-6`).
- **Dimensional analysis tests:** passing incompatible units raises `UnitDimensionError`; `60 rpm == 1.0 1/s` (no $2\pi$ factor error).
- **Missing-evidence tests:** omitting any required input returns `status = "insufficient_evidence"` with exact `missing_inputs` list and `output = None`.
- **Risk & compatibility tests:** every rule (`R-*`) and check (`C-*`) tested for `triggered`/`compatible`, `not_triggered`/`incompatible`, `insufficient_evidence`/`cannot_evaluate`, and `not_configured` (when thresholds are `null`).
- **Determinism & snapshot test:** running `run_assessment` twice on the same `AssessmentInput` yields identical output.

### 2.2 Backend API (`backend/tests/`)
- Auth & tenancy isolation tests (User in Org A gets `404` accessing Org B's project/vessel/batch/assessment).
- Ingestion pipeline tests: upload CSV/XLSX → preview → map → dry-run quality checks (`DQ-*`) → import → query measurements & summary.
- End-to-end API flow test: create project → passport v1 → upload & import 2 batches → create 2 vessels → compare vessels → create scenario → run assessment → update validation task → submit review sign-off → generate PDF report.

### 2.3 Frontend (`frontend/`)
- Type-checking (`tsc --noEmit`), linting, and component tests for quantity/calculation/risk rendering.

## 3. MVP success metrics (CONFIRMED `[BP p.14]`)
- **Data import success:** ≥90% of files in the agreed MVP schema imported without manual rework.
- **Calculation correctness:** 100% pass on agreed unit-test set; no unresolved critical errors.
- **Traceability:** 100% of supported calculations display visible inputs, units and assumptions.
- **Workflow completion:** ≥3 supervised external users complete the workflow without founder intervention.
- **Customer evidence:** 10–15 interviews and ≥1 pilot design partner.
