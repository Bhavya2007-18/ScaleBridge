# 16 — User Workflows

**Purpose:** Trace the end-to-end user journeys across the six Blueprint stages `[BP p.4]`.
**Related:** [02_PROBLEM_AND_SOLUTION.md](02_PROBLEM_AND_SOLUTION.md) · [08_API_SPECIFICATION.md](08_API_SPECIFICATION.md) · [15_UI_UX_SPECIFICATION.md](15_UI_UX_SPECIFICATION.md)

---

## 1. End-to-end workflow overview (CONFIRMED `[BP p.4]`)

```mermaid
sequenceDiagram
  actor Scientist
  actor Reviewer as Bioprocess Engineer / Reviewer
  participant UI as Next.js Web App
  participant API as FastAPI Backend
  participant Sci as scalebridge_science

  Scientist->>UI: 1. Create Project & Process Passport v1
  UI->>API: POST /projects, POST /passport-versions
  API-->>UI: Passport + Data Checklist

  Scientist->>UI: 2. Upload CSV/XLSX batch file & map columns
  UI->>API: POST /files → PUT /mapping → POST /dry-run
  API->>Sci: Normalize units & run DQ checks
  API-->>UI: QualityReport (non-blocking)
  Scientist->>UI: Confirm & Commit Batch Import
  UI->>API: POST /files/{id}/import
  Scientist->>UI: Inspect & overlay 2 batches on Process Dashboard

  Scientist->>UI: 3. Create/select Source (2 L) & Target (150 L) Vessel Profiles
  UI->>API: POST /vessels, GET /vessels/compare
  API-->>UI: Comparable profiles + missing-spec warnings

  Scientist->>UI: 4. Configure Scale-Up Scenario & Run Assessment
  UI->>API: POST /scenarios, POST /scenarios/{id}/assessments
  API->>Sci: run_assessment(AssessmentInput)
  Sci-->>API: Calculations + Trade-offs + RiskFlags + Compatibility + Tasks
  API-->>UI: Immutable Assessment

  Scientist->>UI: 5. Review risks, compatibility & validation tasks
  Reviewer->>UI: Record expert review sign-off
  UI->>API: POST /assessments/{id}/reviews

  Scientist->>UI: 6. Generate & download PDF Transfer Report
  UI->>API: POST /assessments/{id}/reports, GET /reports/{id}/download
```

## 2. Detailed workflows

### WF-1: Create Process Passport & inspect Data Checklist
1. User creates a project (`name`, `product_family`, `organism_name`, `process_type`, `is_synthetic_demo`).
2. User enters Passport v1: recipe version, medium properties ($\rho, \mu, C^*$ if known, with provenance), setpoints (temperature, pH, DO), and feed strategy.
3. System immediately computes `GET /projects/{id}/data-checklist` showing which downstream formulas are ready vs blocked by missing medium or vessel data.

### WF-2: Import batch data & compare batches
1. User uploads CSV/XLSX and declares `is_synthetic` and `source_description`.
2. Preview displays detected columns; user maps columns to canonical variables (`ph`, `dissolved_oxygen`, `temperature`, `agitation_speed`, `airflow`, etc.) and selects units and timestamp mode (`elapsed` or `absolute`).
3. User runs **Dry-Run Validation** (`POST /files/{id}/dry-run`): inspects row count, missing counts, unit conversions, and `DQ-*` issues.
4. If no blocking issues exist, user enters batch metadata (`run_code`, `working_volume`, vessel link) and commits import.
5. User repeats for a second batch and opens the **Process Dashboard** to overlay both batches by elapsed hours.

### WF-3: Describe and compare vessels
1. User creates source benchtop vessel (e.g., 2 L) and target pilot vessel (e.g., 150 L / 200 L) with geometry, impeller type/diameter/$N_p$, motor limits, agitation/aeration ranges, cooling capacity, instrumentation, and any $k_La$ evidence points.
2. UI highlights missing specifications (`missing_specifications` list).
3. User opens `/vessels` comparison view to verify geometric ratios ($D/T$, $H_L/T$) and capability envelopes side-by-side.

### WF-4: Run scale-up scenario & review readiness
1. User selects source batch(es), source vessel version, target vessel version, target working volume, primary criterion (e.g., `S-PV`), secondary criteria (`S-TIP`, `S-KLA`), aeration basis (`S-VVM` or `S-VS`), constraints, and explicit assumptions.
2. User clicks **Run Assessment**.
3. User inspects:
   - **Calculations tab:** source and target descriptors with full equations, inputs, units, provenance, and assumptions.
   - **Trade-offs tab:** side-by-side matrix showing how holding $P/V$ constant changes tip speed and $Re$, and vice versa.
   - **Equipment Compatibility tab:** check outcomes (`compatible`, `incompatible`, `cannot_evaluate`).
   - **Risk Register tab:** flags grouped by category (`oxygen_transfer`, `mixing`, `thermal`, `equipment`, `data`) with clickable evidence links.

### WF-5: Plan validation, sign off, and export Transfer Report
1. User opens **Validation Planner** tab: reviews generated `P1`/`P2`/`P3` tasks, updates statuses or records a waiver with mandatory reason.
2. Reviewer records a sign-off decision (`approved_for_discussion` or `changes_requested`) with commentary.
3. User generates a versioned PDF **Transfer Report** containing all sections, disclaimers, and synthetic-data watermark (if applicable).
