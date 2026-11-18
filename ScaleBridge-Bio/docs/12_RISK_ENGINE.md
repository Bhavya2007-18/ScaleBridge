# 12 — Scale-up Risk Engine

**Purpose:** Specify the rule-based Scale-up Risk Engine: rule registry, outcomes, severities, thresholds, explanations and links to evidence gaps.
**Related:** [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md) · [13_EQUIPMENT_COMPATIBILITY.md](13_EQUIPMENT_COMPATIBILITY.md) · [14_VALIDATION_PLANNER.md](14_VALIDATION_PLANNER.md)

---

## 1. Requirements (CONFIRMED `[BP p.4, p.5, p.10]`)
- Compare engineering constraints; highlight where scale-up criteria **conflict** or **cannot be evaluated** due to missing data.
- Rule-based warnings for **oxygen transfer, mixing, thermal capability, missing data and equipment limits**.
- **Every flag links to a specific input, rule and evidence gap** (acceptance test).
- Output an explainable risk register with confidence and missing evidence; uncertainty labels.
- Start rule-based (not ML); human sign-off on outputs `[BP p.15]`.

## 2. Design (PROPOSED)
- Rules are pure functions in `scalebridge_science/readiness/rules/`, registered in a versioned registry (`RULE_REGISTRY_VERSION`).
- Signature: `evaluate(ctx: RuleContext) -> list[RiskFlag]` where `RuleContext` = `AssessmentInput` + computed `CalculationResult`s + `CompatibilityCheck`s + `ThresholdConfig`.
- Rules **never** read the DB, never invent numbers, and must emit a flag for every evaluation — including `not_triggered`, so the register shows what was checked.

### 2.1 Outcomes
| Outcome | Meaning | Shown as |
|---|---|---|
| `triggered` | Rule condition met — a risk is present | Coloured by severity |
| `not_triggered` | Evaluated with sufficient evidence; condition not met | "Checked — no issue" (grey/green) |
| `insufficient_evidence` | Required inputs missing/unusable | "Insufficient evidence" (amber outline) — a first-class result `[BP p.4]` |
| `not_configured` | Rule needs a threshold that the scientific lead has not set | "Not evaluated — threshold not configured" |

### 2.2 Severity (PROPOSED scale; defaults per rule below, overridable only via threshold config by Person 1)
`critical` (transfer as specified is not possible with documented equipment) · `high` (likely to compromise the pilot run or makes a key criterion unevaluable) · `medium` · `low` · `info`.

### 2.3 RiskFlag contract
```json
{
  "rule_id": "R-OXY-003",
  "rule_version": "1.0.0",
  "category": "oxygen_transfer",
  "severity": "high",
  "outcome": "triggered",
  "title": "Target oxygen transfer capacity below observed oxygen demand",
  "explanation": "At the S-PV operating point, OTR in the target vessel at the required DO (20 % air sat) is 9.8 mmol/(L·h) using kLa evidence point 'kla-2' (vendor_datasheet, measured in water at different gas flow). Peak OUR in source batches B-01/B-02 is 14.0 mmol/(L·h) (user-supplied).",
  "input_refs": [
    { "kind": "calculation", "ref_id": "<calc uuid>", "key": "F-OTR-001:target:S-PV" },
    { "kind": "measurement_summary", "ref_id": "<batch uuid>", "key": "our:max" },
    { "kind": "vessel_parameter", "ref_id": "<vessel_version uuid>", "key": "kla_evidence:kla-2" }
  ],
  "evidence_gap": "kLa measured in the target vessel at the planned agitation/aeration range in process-relevant medium",
  "threshold_used": { "otr_demand_margin": null },
  "validation_task_codes": ["VT-KLA-TARGET", "VT-REVIEW-OXY"]
}
```
*(Numbers illustrative.)* Explanations are generated from templates with actual values and units; free-text LLM generation is prohibited.

## 3. Threshold configuration (PROPOSED structure; **values: OQ-013**)
Owned by Person 1 (scientific lead), versioned (`threshold_config_version`), snapshotted into each assessment. **Every value defaults to `null`**; a rule depending on a `null` threshold returns `not_configured`. Agents must not fill in numbers.

| Key | Used by | Meaning |
|---|---|---|
| `re_turbulent_min` | R-MIX-003 | Minimum Re considered turbulent for the configured impeller types |
| `descriptor_ratio_band.{p_per_v,u_tip,re,vvm,v_s}` | R-MIX-001 | Allowed `[min,max]` ratio target/source for non-preserved descriptors |
| `geometric_similarity_tolerance.{d_over_t,hl_over_t}` | R-MIX-004 | Max relative difference between scales |
| `otr_demand_margin` | R-OXY-003 | Required fractional margin of OTR over OUR (null ⇒ plain comparison, flagged "no margin configured") |
| `cooling_margin` | R-THM-002 | Required fractional margin of cooling capacity over heat load (null ⇒ plain comparison) |
| `temperature_deviation_max` | R-THM-003 | Max acceptable |T − T_set| in source batches |
| `do_critical_percent` | R-OXY-001 | Organism/process-specific critical DO (alternatively per-scenario `min_do_required` constraint) |

## 4. Rule registry (MVP)

Format: **ID — title** · category · default severity · inputs · logic · outcome conditions · evidence gap · validation task(s).

### 4.1 Data (`data`)
| ID | Title | Sev. | Logic | Outcomes | Evidence gap → task |
|---|---|---|---|---|---|
| R-DAT-001 | Required input missing for calculation/criterion | high if primary criterion, else medium | For each `CalculationResult` with status `insufficient_evidence` | `insufficient_evidence` per missing group; `not_triggered` if none | Named missing inputs → `VT-DATA-<input>` (data_request) |
| R-DAT-002 | Key result depends on assumed values | medium | Any result used by a primary criterion, R-OXY-003 or R-EQP-* has `evidence_level = assumed` | triggered / not_triggered | Replace assumption with measurement → `VT-MEASURE-<input>` |
| R-DAT-003 | Source data quality issues affect inputs | medium | Any `high`/`critical` DQ issue (doc 09 §7) on a variable used in §2.3 of doc 11, or invalid points excluded from it | triggered / not_triggered | Review/clean source data → `VT-DATA-QUALITY` |
| R-DAT-004 | Sensor calibration status unknown | low | DO or pH column used with `calibration_status ∈ {unknown, not_calibrated}` | triggered / not_triggered | Calibration records → `VT-DATA-CALIBRATION` |
| R-DAT-005 | Synthetic or demonstration data | info | `is_synthetic = true` on any input | triggered / not_triggered | Replace with real dataset → `VT-DATA-REAL` |
| R-DAT-006 | Formula pending expert review used | info | Any result from formula with `review_status = pending_review` | triggered / not_triggered | Expert review → `VT-REVIEW-FORMULAS` |

### 4.2 Oxygen transfer (`oxygen_transfer`)
| ID | Title | Sev. | Logic | Outcomes | Evidence gap → task |
|---|---|---|---|---|---|
| R-OXY-001 | Source DO fell below required level | high | `DO_min(source) < min_do_required` (scenario) else `< do_critical_percent` | triggered / not_triggered / not_configured (neither set) / insufficient (no DO data) | Confirm whether lab process was already O₂-limited → `VT-REVIEW-OXY`, `VT-EXP-DO-PROFILE` |
| R-OXY-002 | No kLa evidence for target vessel | high | Target vessel has no kLa evidence point selected | insufficient_evidence / not_triggered | kLa in target vessel over planned range → `VT-KLA-TARGET` |
| R-OXY-003 | Target OTR capacity below oxygen demand | high | `OTR_target(at DO_req, op. point of each agitation criterion) < OUR_max(source)·(1+margin)` | triggered / not_triggered / insufficient (no OUR, no OTR) | kLa target, OUR data → `VT-KLA-TARGET`, `VT-MEASURE-OUR` |
| R-OXY-004 | kLa evidence not representative | medium | Selected kLa point has `KLA_CONDITIONS_MISMATCH`, or provenance `published_correlation`/`user_assumption`, or medium description differs from passport medium | triggered / not_triggered / insufficient (no kLa) | Process-relevant kLa → `VT-KLA-TARGET` / `VT-KLA-SOURCE` |
| R-OXY-005 | No kLa evidence for source vessel | medium | Source vessel has no kLa point selected | insufficient_evidence / not_triggered | → `VT-KLA-SOURCE` |

### 4.3 Mixing / hydrodynamics (`mixing`)
| ID | Title | Sev. | Logic | Outcomes | Evidence gap → task |
|---|---|---|---|---|---|
| R-MIX-001 | Criterion trade-off outside acceptable band / constraint | high if user constraint violated, else medium | For each agitation criterion: non-preserved descriptor ratio outside `descriptor_ratio_band`, or target value violates user constraint (`max_tip_speed`, `max_p_per_v`, `max_vvm`) | triggered / not_triggered / not_configured (no band & no constraint) | Expert decision on criterion priority → `VT-REVIEW-CRITERIA` |
| R-MIX-002 | No mixing-time evidence | medium | No mixing_time evidence for target (and source) | insufficient_evidence / not_triggered | Mixing study → `VT-MEASURE-MIXING` |
| R-MIX-003 | Flow regime outside turbulent assumption | medium | Re (source or target, any criterion) `< re_turbulent_min` | triggered / not_triggered / not_configured / insufficient (no μ/ρ) | Viscosity data, review of N_p validity → `VT-MEASURE-VISCOSITY`, `VT-REVIEW-FORMULAS` |
| R-MIX-004 | Vessels not geometrically similar | medium | Impeller type or count differs (pure logic), or D/T, H_L/T relative difference > tolerance | triggered / not_triggered / not_configured (ratios only) / insufficient (geometry missing) | Expert review of transferability → `VT-REVIEW-GEOMETRY` |

### 4.4 Thermal (`thermal`)
| ID | Title | Sev. | Logic | Outcomes | Evidence gap → task |
|---|---|---|---|---|---|
| R-THM-001 | Target cooling capacity undocumented | high | Target `cooling_capacity` missing | insufficient_evidence / not_triggered | Vendor/facility cooling spec → `VT-DATA-COOLING` |
| R-THM-002 | Heat load may exceed cooling capacity | high | `estimated_heat_load·(1+cooling_margin) > cooling_capacity` | triggered / not_triggered / insufficient (heat load missing) | Heat balance by engineer → `VT-REVIEW-THERMAL` |
| R-THM-003 | Temperature control deviation in source batches | low | max |T − T_set| > `temperature_deviation_max` | triggered / not_triggered / not_configured / insufficient (no setpoint) | → `VT-REVIEW-THERMAL` |

### 4.5 Equipment (`equipment`) — derived from compatibility checks ([13](13_EQUIPMENT_COMPATIBILITY.md) §4)
| ID | Title | Sev. | Logic | Evidence gap → task |
|---|---|---|---|---|
| R-EQP-001 | Required agitation outside target range | critical (primary criterion) / high | `C-AGIT-RANGE` incompatible | → `VT-REVIEW-EQUIPMENT` |
| R-EQP-002 | Required power exceeds motor limit | critical / high | `C-MOTOR-POWER` incompatible | → `VT-REVIEW-EQUIPMENT`, `VT-MEASURE-POWER` |
| R-EQP-003 | Required gas flow outside target range | critical / high | `C-GAS-RANGE` incompatible | → `VT-REVIEW-EQUIPMENT` |
| R-EQP-004 | Target volume outside vessel working range | critical | `C-VOLUME-RANGE` incompatible | → `VT-REVIEW-EQUIPMENT` |
| R-EQP-005 | Required instrumentation/control unavailable | high | `C-INSTRUMENT` incompatible | → `VT-REVIEW-EQUIPMENT` |
| R-EQP-006 | Capability envelope incomplete | medium | Any `C-*` = `cannot_evaluate` | → `VT-DATA-VESSEL-SPEC` |

Severity for R-EQP-001…003: `critical` when the failing operating point is from the **primary** criterion, `high` otherwise.

## 5. Assessment summary roll-up (PROPOSED)
- Counts by severity for `triggered`; counts of `insufficient_evidence` and `not_configured`.
- **No single "readiness score"** in MVP (it would imply validated weighting — **OQ-034**). The headline is: *n critical, n high, n insufficient-evidence items*, plus overall evidence level.

## 6. Acceptance criteria
1. Each rule has tests for every outcome it can produce (triggered / not_triggered / insufficient_evidence / not_configured).
2. Every emitted flag has non-empty `input_refs`, `rule_id`, `rule_version`; flags with outcome ≠ `not_triggered` have `evidence_gap` (Blueprint acceptance test).
3. With an all-`null` threshold config, no rule fabricates a threshold (tests assert `not_configured`).
4. Explanation templates render units and values from inputs (snapshot tests).
5. Rule changes bump `RULE_REGISTRY_VERSION` and require Person 1 + Person 2 review.
