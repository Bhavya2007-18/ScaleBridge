# 10 — Scientific Engine

**Purpose:** Specify the design of `scalebridge_science`, the product's **trust layer** `[BP p.6]`: unit handling, formula registry, provenance, evidence labelling, versioning and review workflow. Equations themselves are in [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md); rules in [12_RISK_ENGINE.md](12_RISK_ENGINE.md).
**Related:** [05_SYSTEM_ARCHITECTURE.md](05_SYSTEM_ARCHITECTURE.md) · [13_EQUIPMENT_COMPATIBILITY.md](13_EQUIPMENT_COMPATIBILITY.md) · [14_VALIDATION_PLANNER.md](14_VALIDATION_PLANNER.md) · [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md)

---

## 1. Principles (CONFIRMED `[BP p.4, p.6, p.10, p.11]`)
1. Deterministic, unit-tested calculations and process-specific assumptions.
2. No single scale-up criterion is universally appropriate; preserving one changes others [S12, S13].
3. Store original values and units; convert to an agreed internal unit system with a unit-aware library.
4. Record provenance: sensor, manual entry, lab assay, vendor datasheet, published correlation, user assumption.
5. Separate measured values from estimates; a calculated estimate must never be displayed as a measurement.
6. Display equipment and medium assumptions required by each calculation.
7. Report trade-offs; never imply constant kLa, P/V, tip speed and mixing time can all be preserved simultaneously.
8. Version equations, correlations, vessel profiles and reports so a result can be reproduced.
9. Deterministic equations first; ML only later with real governed data; optimization (CasADi/GEKKO) optional later.

## 2. Package layout (PROPOSED)

```
backend/scalebridge_science/
├── __init__.py            # ENGINE_VERSION, CONTRACT_VERSION
├── contracts.py           # Pydantic I/O models (Quantity, AssessmentInput, AssessmentOutput…)
├── units.py               # shared Pint UnitRegistry + custom units + display conversions
├── evidence.py            # value_nature / evidence_level derivation
├── formulas/
│   ├── registry.py        # FORMULA_REGISTRY_VERSION, Formula metadata objects
│   ├── oxygen.py          # F-OTR-001
│   ├── hydrodynamics.py   # F-PV-001, F-TIP-001, F-RE-001, F-PWR-001
│   └── aeration.py        # F-VVM-001, F-VS-001
├── criteria/
│   ├── registry.py        # S-PV, S-TIP, S-VVM, S-KLA
│   └── tradeoffs.py       # target operating point + descriptor ratios
├── readiness/
│   ├── rules/             # R-OXY-*, R-MIX-*, R-THM-*, R-DAT-*, R-EQP-*
│   ├── registry.py        # RULE_REGISTRY_VERSION
│   ├── thresholds.py      # ThresholdConfig model (values owned by scientific lead)
│   ├── compatibility.py   # C-* checks
│   └── validation.py      # gap → ValidationTask templates
├── pipeline.py            # run_assessment(AssessmentInput) -> AssessmentOutput
└── tests/                 # known-value, dimensional, property, regression tests
```

**Hard boundary:** this package imports only the standard library, `numpy`, `scipy`, `pandas`, `pint`, `pydantic`. No FastAPI, SQLAlchemy, HTTP, file system, environment variables, clock or randomness (NFR-06).

## 3. Internal unit system (PROPOSED — **OQ-017**)
SI base units internally; display units chosen per variable for bioprocess familiarity.

| Quantity | Internal (SI) | Display |
|---|---|---|
| Length (D, T, H) | m | mm / m |
| Volume | m³ | L |
| Rotational speed N | 1/s (revolutions per second) | rpm |
| Power P | W | W / kW |
| Power per volume | W/m³ | kW/m³ (= W/L) |
| Velocity (u_tip, v_s) | m/s | m/s |
| Density ρ | kg/m³ | kg/m³ |
| Dynamic viscosity μ | Pa·s | mPa·s |
| Gas volumetric flow Q_g | m³/s | L/min |
| vvm | 1/s internally | 1/min (vvm) |
| kLa | 1/s | 1/h |
| O₂ concentration (C*, C_L) | mol/m³ | mmol/L |
| OTR, OUR | mol/(m³·s) | mmol/(L·h) |
| Temperature | K | °C |
| Pressure | Pa (absolute) | bar(a) |

DO in `% air saturation` has its own dimension and is converted to concentration **only** via an explicit C* input: `C_L = (DO%/100) · C*`. This conversion is itself a recorded calculation (F-DOC-001, [11](11_SCALE_UP_CALCULATIONS.md) §3.2).

## 4. Contracts (PROPOSED; `CONTRACT_VERSION` semver)

```python
# illustrative type signatures only — not implementation
class Quantity(BaseModel):
    value: float            # SI value
    unit: str               # SI unit string, e.g. "m", "1/s"
    original_value: float | None
    original_unit: str | None
    provenance: Provenance  # sensor | manual_entry | lab_assay | vendor_datasheet | published_correlation | user_assumption | calculated
    value_nature: ValueNature  # measured | estimated | assumed | calculated
    source_ref: str | None  # e.g. "vessel_parameter:<uuid>", "batch_summary:<batch>:agitation_speed:median"
    note: str | None

class VesselSpec(BaseModel):
    vessel_version_id: str
    scale_class: str
    impeller_type: str | None
    impeller_count: int | None
    sparger_type: str | None
    instrumentation: list[str]
    controls: list[str]
    parameters: dict[str, Quantity]  # keys from 13_EQUIPMENT_COMPATIBILITY §3.2

class ProcessSummary(BaseModel):         # derived from source batches
    batch_ids: list[str]
    aggregation: str                     # e.g. "per-variable statistic across batches (see doc 11 §2.3)"
    operating: dict[str, Quantity]       # agitation_speed, airflow, working_volume, temperature, headspace_pressure
    extremes: dict[str, Quantity]        # do_min, our_max (if supplied), temperature_max_deviation...
    data_quality: dict[str, int]         # counts of invalid/suspect points used/excluded

class MediumProperties(BaseModel):
    density: Quantity | None
    viscosity: Quantity | None
    oxygen_saturation_concentration: Quantity | None  # C*

class ScenarioConfig(BaseModel):
    criteria: list[CriterionSelection]   # criterion_id, is_primary
    target_working_volume: Quantity
    constraints: dict[str, Quantity]
    thresholds: ThresholdConfig          # snapshot (doc 12 §4)

class AssessmentInput(BaseModel):
    contract_version: str
    source_vessel: VesselSpec
    target_vessel: VesselSpec
    process: ProcessSummary
    medium: MediumProperties
    scenario: ScenarioConfig
    is_synthetic: bool

class CalculationResult(BaseModel):
    formula_id: str; formula_version: str; review_status: str
    scale: Literal["source", "target"]; criterion_id: str | None
    equation: str                         # human-readable, e.g. "u_tip = π · N · D"
    inputs: dict[str, Quantity]
    output: Quantity | None
    status: Literal["computed", "insufficient_evidence", "not_applicable", "error"]
    missing_inputs: list[str]
    evidence_level: EvidenceLevel
    assumptions: list[str]; warnings: list[str]

class AssessmentOutput(BaseModel):
    engine_version: str; formula_registry_version: str; rule_registry_version: str
    calculations: list[CalculationResult]
    trade_offs: list[TradeOff]            # doc 11 §8
    risk_flags: list[RiskFlag]            # doc 12
    compatibility_checks: list[CompatibilityCheck]  # doc 13
    validation_tasks: list[ValidationTask]          # doc 14
    summary: AssessmentSummary
```

## 5. Formula registry (PROPOSED structure)
Each formula is declared with metadata the UI and report render directly (FR-SC-03):

| Field | Example (F-TIP-001) |
|---|---|
| `formula_id` / `version` | `F-TIP-001` / `1.0.0` |
| `name` | Impeller tip speed |
| `equation_text` / `equation_latex` | `u_tip = π · N · D` / `u_{tip} = \pi N D` |
| `variables` | `N`: rotational speed [1/s]; `D`: impeller diameter [m] |
| `output` | `u_tip` [m/s] |
| `source_basis` | `Blueprint p.6` (+ literature reference once confirmed by scientific lead) |
| `blueprint_status` | `confirmed` (listed in Blueprint) or `proposed` |
| `review_status` | `draft` → `pending_review` → `approved` → `deprecated` |
| `assumptions` | list of strings |
| `validity_limits` | list of strings (e.g., "single impeller diameter; for multiple impellers, D of each impeller evaluated separately") |
| `required_inputs` | names + where they come from |

**Execution policy (PROPOSED):**
- `draft` formulas are never executed in assessments.
- `pending_review` formulas execute but every result carries warning `FORMULA_PENDING_REVIEW` shown in UI and report.
- `approved` requires Person 1 + Person 2 sign-off (and external advisor for `proposed` formulas), recorded in `docs/` formula register changelog with date and reviewer names (`[BP p.13]`: every formula change reviewed by both).

## 6. Missing data & "insufficient evidence" semantics (CONFIRMED principle `[BP p.4, p.11]`)
- A formula with any missing required input returns `status = insufficient_evidence`, `output = null`, `missing_inputs = [...]`. **No defaults are ever substituted by the engine.**
- Users may supply explicit **assumptions** (provenance `user_assumption`, nature `assumed`). The engine then computes, but the result's `evidence_level` is at best `assumed` and the assumption is listed.
- A formula whose validity limits are violated (e.g., flow regime outside the range assumed by a power-number estimate) returns `computed` with a warning **and** triggers the relevant rule; it is never silently dropped.
- Division by zero / non-finite → `status = error` with message; the assessment still completes.

## 7. Evidence level derivation (PROPOSED; implements "confidence"/"uncertainty labels" `[BP p.4, p.10]`)

The evidence level of a calculated result is the **weakest** nature among its inputs:

| All inputs measured | ≥1 estimated, none assumed | ≥1 assumed | any missing |
|---|---|---|---|
| `measured` (*calculated from measured inputs*) | `estimated` | `assumed` | `insufficient` |

Mixed descriptors across a criterion's outputs roll up as `mixed` in the assessment summary. The UI label for a computed value is always "**Calculated**" plus the evidence level, never "Measured" (NFR-12).

> This is an **ordinal transparency label**, not a quantitative uncertainty. Quantitative uncertainty propagation (e.g., interval or Monte Carlo) is **not** in MVP and must not be implied (**OQ-033**).

## 8. Versioning & reproducibility (CONFIRMED `[BP p.11]`)
- Constants: `ENGINE_VERSION`, `CONTRACT_VERSION`, `FORMULA_REGISTRY_VERSION`, `RULE_REGISTRY_VERSION`; threshold config has its own version string.
- Any change in numerical behaviour → bump `ENGINE_VERSION` + affected registry version + changelog entry.
- Assessments persist the full `AssessmentInput` snapshot and all versions; historical assessments are never recomputed in place. A "re-run" creates a new assessment.
- Regression suite: stored snapshots of reference assessments must reproduce exactly (float tolerance `rel=1e-12`) unless the version is bumped and snapshots re-approved.

## 9. Formula & assumption register (CONFIRMED deliverable of Person 1 `[BP p.13]`, `[BP p.16]` action 10)
The register is generated from the code registry (`GET /science/formulas`) and exported to the report appendix. It lists for every formula: equation, variables/units, assumptions, validity limits, source basis, review status, reviewer, date.

## 10. Error handling summary
| Situation | Output |
|---|---|
| Missing input | `insufficient_evidence` + `missing_inputs` |
| Input dimensionality wrong | Raises `UnitDimensionError` → assessment `failed` (programming/contract error, should be prevented by API validation) |
| Non-finite result | `error` status for that calculation only |
| Rule threshold not configured | rule outcome `not_configured` ([12](12_RISK_ENGINE.md)) |
| Unknown criterion / formula ID | Validation error at API boundary (422) |

## 11. Acceptance criteria
- 100% of registry formulas have known-value tests, dimensional tests and an `insufficient_evidence` test.
- `mypy --strict` passes for the package; import-linter (or equivalent test) proves no forbidden imports.
- Every `CalculationResult` in a reference assessment has non-empty `equation`, `inputs` with units/provenance, and `assumptions` (traceability metric 100% `[BP p.14]`).
