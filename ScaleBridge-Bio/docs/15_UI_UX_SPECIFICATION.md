# 15 — UI/UX Specification

**Purpose:** Specify the screen hierarchy, navigation, scientific display rules, component patterns and visual design standards for the Next.js web application.
**Related:** [03_PRODUCT_REQUIREMENTS.md](03_PRODUCT_REQUIREMENTS.md) · [08_API_SPECIFICATION.md](08_API_SPECIFICATION.md) · [16_USER_WORKFLOWS.md](16_USER_WORKFLOWS.md)

---

## 1. Design principles (CONFIRMED `[BP p.4–6]`, visual tokens PROPOSED)
1. **Process engineer's workspace, not a marketing dashboard:** high information density, tabular clarity, zero decorative noise.
2. **Every number has a unit, provenance badge, and value-nature badge:** never render a bare float.
3. **Measured vs Calculated vs Estimated vs Assumed:** visually distinct badges on every parameter and calculation output (`[BP p.6]`).
4. **"Insufficient evidence" is first-class:** rendered as a clear amber/neutral structured card listing the missing inputs—never as a broken widget, `NaN`, `-`, or `0`.
5. **Synthetic data banner:** persistent top bar whenever `is_synthetic_demo` or `is_synthetic` is true (`[BP p.5]`).

## 2. Visual system (PROPOSED)
- **Palette:** Deep Navy (`#0B192C`) primary header/sidebar (matching Blueprint cover), Teal (`#0D9488`) engineering accent, Slate (`#F8FAFC` / `#1E293B`) surfaces and text.
- **Semantic status colors:**
  - `critical`: `#DC2626` (Red 600)
  - `high`: `#EA580C` (Orange 600)
  - `medium`: `#D97706` (Amber 600)
  - `low` / `info`: `#2563EB` (Blue 600)
  - `compatible` / `not_triggered`: `#059669` (Emerald 600)
  - `insufficient_evidence` / `cannot_evaluate`: `#78716C` border + `#FEF3C7` background
- **Typography:** Inter / system sans for UI; JetBrains Mono (or monospace) for numerical tables, equations, units and SHA-256 hashes.

## 3. Navigation & route map (PROPOSED)
Left sidebar + top breadcrumb bar + organization switcher + 4-stage workflow progress bar (`01 LAB DATA` → `02 ENGINEERING` → `03 RISK REVIEW` → `04 TRANSFER` `[BP p.1]`).

| Route | Screen | Primary components |
|---|---|---|
| `/login` | Sign in | Email/password form |
| `/projects` | Projects & Passports list | Project cards, Create Project modal, Synthetic badge |
| `/projects/[id]/passport` | Stage 01 — Process Passport | Version selector, organism/medium/parameter forms, Data Checklist panel |
| `/projects/[id]/batches` | Stage 01 — Batch Ingestion & Dashboard | File Upload wizard (Upload → Map → Dry-Run Quality Report → Commit), Plotly multi-axis trend viewer & multi-batch overlay |
| `/vessels` | Stage 02 — Vessel Library & Comparison | Vessel list, Versioned Parameter Editor (with provenance), Missing-Spec warning banner, Side-by-Side Comparison table |
| `/projects/[id]/scenarios` | Stage 02 — Scale-Up Scenarios | Scenario builder (batches, source/target vessels, target volume, criteria, constraints, assumptions), Run Assessment trigger |
| `/assessments/[id]` | Stage 03 — Readiness & Risk Review | Summary header, Calculation Cards (equation + inputs + assumptions), Criterion Trade-Off Matrix, Compatibility Table, Explainable Risk Register |
| `/assessments/[id]/validation` | Stage 04 — Validation & Transfer | Prioritized Validation Tasks table (status/waiver editor), Reviewer Sign-Off panel, Generate & Download PDF Transfer Report |

## 4. Reusable scientific UI components
1. `<QuantityInput />`: numeric input + unit selector (filtered by canonical variable) + provenance selector + value-nature badge + source reference input.
2. `<QuantityDisplay />`: renders `1.44 m/s (8.33 1/s · 0.055 m)` with tooltip showing SI value, original value, provenance and conversion factor.
3. `<CalculationCard />`: header (formula name, version, review status badge), LaTeX/formatted equation, input table with provenance, output with evidence-level badge, collapsible assumptions & warnings list, or `<InsufficientEvidenceBox />` when status is `insufficient_evidence`.
4. `<TradeOffMatrix />`: rows = descriptors ($P/V$, $u_{tip}$, $Re$, $vvm$, $v_s$, $OTR$), columns = selected criteria (`S-PV`, `S-TIP`, …), cells = target value + `target/source` ratio + compatibility badge.
5. `<RiskFlagCard />`: severity pill, outcome pill, rule ID/version, explanation text, clickable chips for every `input_ref`, highlighted `evidence_gap`, and linked validation task codes.
6. `<BatchTrendChart />`: Plotly wrapper supporting synchronized x-axis (`elapsed_s` in hours), multi-batch overlay, quality-flag styling (`suspect` hollow markers, `invalid` hidden by default with toggle, gaps never interpolated).

## 5. Acceptance criteria
- Desktop viewport (`≥1280px`) renders all tables and charts without horizontal page overflow.
- Every calculation card displays equation, units, inputs, provenance, and assumptions (100% traceability `[BP p.14]`).
- No screen displays `undefined`, `NaN`, or unitless numbers.
