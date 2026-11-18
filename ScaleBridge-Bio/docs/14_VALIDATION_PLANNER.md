# 14 — Validation Planner

**Purpose:** Specify how risk flags, compatibility failures and missing-evidence items are converted into a prioritized, actionable validation plan before a pilot run.
**Related:** [12_RISK_ENGINE.md](12_RISK_ENGINE.md) · [13_EQUIPMENT_COMPATIBILITY.md](13_EQUIPMENT_COMPATIBILITY.md) · [07_DATABASE_SCHEMA.md](07_DATABASE_SCHEMA.md) §4.6

---

## 1. Requirements (CONFIRMED `[BP p.4, p.10]`)
- Convert gaps into a prioritized list of **measurements, experiments and expert reviews** needed before a pilot run (`data_request` added as fourth type — PROPOSED).
- Link each validation task to the risk flag(s) and compatibility check(s) that triggered it.
- Include the validation plan in the Transfer Report `[BP p.5]`.

## 2. Design (PROPOSED)
Pure function `generate_validation_tasks(flags, checks) -> list[ValidationTask]` in `scalebridge_science/readiness/validation.py`. Deduplicates tasks by `task_code`, merges `linked_risk_flag_ids` and `linked_check_ids`, and assigns the highest priority demanded by any linked item.

### 2.1 Priority mapping
| Highest linked severity / outcome | Task priority | Meaning |
|---|---|---|
| `critical` or (`high` + primary criterion) | `P1` | Must resolve before committing to pilot run |
| `high` or `insufficient_evidence` on core descriptor | `P2` | Should resolve before finalizing operating parameters |
| `medium`, `low`, `info` | `P3` | Recommended documentation / verification improvement |

### 2.2 Task template registry (MVP)
| Task code | Type | Title | Default priority | Triggered by rules / checks |
|---|---|---|---|---|
| `VT-KLA-TARGET` | `measurement` | Measure or obtain verified $k_La$ in target vessel across planned $(N, Q_g)$ range | P1 | `R-OXY-002`, `R-OXY-003`, `R-OXY-004` |
| `VT-KLA-SOURCE` | `measurement` | Measure $k_La$ in source lab vessel at reference operating point | P2 | `R-OXY-004`, `R-OXY-005` |
| `VT-MEASURE-OUR` | `measurement` | Quantify peak oxygen uptake rate (OUR) in lab process | P1 | `R-OXY-003`, `R-DAT-001` (OUR) |
| `VT-EXP-DO-PROFILE` | `experiment` | Verify DO sensitivity and minimum acceptable DO in bench-scale run | P2 | `R-OXY-001` |
| `VT-REVIEW-OXY` | `expert_review` | Bioprocess engineer review of oxygen transfer balance and gas supply strategy | P1 | `R-OXY-001`, `R-OXY-003` |
| `VT-REVIEW-CRITERIA` | `expert_review` | Bioprocess engineer review of scale-up criterion selection and descriptor trade-offs | P1 | `R-MIX-001` |
| `VT-MEASURE-MIXING` | `measurement` | Characterize mixing time in target vessel (or review existing facility mixing study) | P2 | `R-MIX-002` |
| `VT-MEASURE-VISCOSITY` | `measurement` | Measure broth density and viscosity (and rheology if non-Newtonian) at process conditions | P2 | `R-MIX-003`, `R-DAT-001/002` ($\mu, \rho$) |
| `VT-REVIEW-GEOMETRY` | `expert_review` | Review geometric and impeller differences between source and target vessels | P2 | `R-MIX-004` |
| `VT-REVIEW-FORMULAS` | `expert_review` | Domain-expert sign-off on pending-review formulas and power-number assumptions | P2 | `R-DAT-006`, `R-MIX-003` |
| `VT-DATA-COOLING` | `data_request` | Request target vessel cooling capacity specification from facility/vendor | P1 | `R-THM-001`, `C-COOLING` |
| `VT-REVIEW-THERMAL` | `expert_review` | Perform metabolic + agitation heat balance against target cooling capability | P1 | `R-THM-002`, `R-THM-003` |
| `VT-REVIEW-EQUIPMENT` | `expert_review` | Resolve target vessel capability incompatibility (adjust volume/criterion or select alternate vessel) | P1 | `R-EQP-001…005` |
| `VT-DATA-VESSEL-SPEC` | `data_request` | Obtain missing target/source vessel specifications from datasheet or facility | P2 | `R-EQP-006`, `C-*` (`cannot_evaluate`) |
| `VT-MEASURE-POWER` | `measurement` | Verify target motor/drive power limit and impeller power number $N_p$ | P2 | `R-EQP-002` |
| `VT-DATA-QUALITY` | `data_request` | Resolve source batch data-quality issues (gaps, invalid readings, timestamp order) | P2 | `R-DAT-003` |
| `VT-DATA-CALIBRATION` | `data_request` | Document pre-run DO and pH probe calibration records | P3 | `R-DAT-004` |
| `VT-DATA-REAL` | `experiment` | Replace synthetic/demo dataset with real laboratory fermentation batch data | P1 | `R-DAT-005` |

## 3. Lifecycle & sign-off
- Tasks start `open`. Scientists can mark `in_progress`, `done`, or `waived` (requires `waived_reason`, audited).
- Waiving or completing a task does **not** alter risk flags of an existing assessment; it is recorded on the assessment and displayed in the report alongside the waiver reason.

## 4. Acceptance criteria
- Every triggered or `insufficient_evidence` risk flag produces at least one `ValidationTask`.
- Duplicate triggers merge into a single task with combined `linked_risk_flag_ids`.
- `PATCH /validation-tasks/{id}` with `status = "waived"` and empty `waived_reason` returns 422.
