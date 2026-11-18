# 11 — Scale-up Calculations

**Purpose:** Define every equation the MVP computes: variables, units, inputs, provenance, assumptions, limitations and validation requirements. Nothing here is a prediction of process performance.
**Related:** [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [12_RISK_ENGINE.md](12_RISK_ENGINE.md) · [13_EQUIPMENT_COMPATIBILITY.md](13_EQUIPMENT_COMPATIBILITY.md) · [18_TESTING_AND_VALIDATION.md](18_TESTING_AND_VALIDATION.md) · [22_OPEN_QUESTIONS.md](22_OPEN_QUESTIONS.md)

> [!IMPORTANT]
> **Blueprint-listed equations** (CONFIRMED `[BP p.6]`): OTR = kLa(C* − C_L); P/V; u_tip = πND; Re = ρND²/μ; vvm = gas flow / liquid working volume; kLa as measured/estimated coefficient.
> **Everything else in this file is PROPOSED** and ships with `review_status = pending_review` until Person 1 + Person 2 + external advisor approve it ([10](10_SCIENTIFIC_ENGINE.md) §5). Test vectors below are **arithmetic checks of the implementation, not physical reference data**.

---

## 1. Formula index

| ID | Name | Equation | Blueprint status | MVP |
|---|---|---|---|---|
| F-OTR-001 | Oxygen transfer rate | OTR = kLa·(C* − C_L) | CONFIRMED | Yes, where data supports |
| F-DOC-001 | DO % → concentration | C_L = (DO/100)·C* | PROPOSED | Yes |
| F-PV-001 | Power per volume | P/V = P / V_w | CONFIRMED | Yes |
| F-PWR-001 | Ungassed power from power number | P₀ = N_p·ρ·N³·D⁵ | PROPOSED (**OQ-012**) | Yes, pending review |
| F-TIP-001 | Impeller tip speed | u_tip = π·N·D | CONFIRMED | Yes |
| F-RE-001 | Impeller Reynolds number | Re = ρ·N·D²/μ | CONFIRMED | Yes |
| F-VVM-001 | Gas flow per volume | vvm = Q_g / V_w | CONFIRMED | Yes |
| F-VS-001 | Superficial gas velocity | v_s = Q_g / (π·T²/4) | PROPOSED ("gas flow descriptors" `[BP p.5]`) | Yes, pending review |
| F-GEO-001 | Geometric ratios | D/T, H_L/T | PROPOSED | Yes |
| F-KLA-000 | kLa | **input only** (measured or documented) | CONFIRMED as descriptor | Input only; correlations excluded (**OQ-011**) |
| S-TIP, S-PV, S-VVM, S-VS, S-KLA | Scale-up criteria | §8 | PROPOSED derivations from the above | Yes, pending review |

Not computed in MVP (accepted only as user-supplied values with provenance): mixing time, heat load / heat balance, OUR/CER from off-gas, C* from Henry's law, gassed power correction, kLa correlations (**OQ-010, OQ-011, OQ-012, OQ-014, OQ-015, OQ-016**).

## 2. Common inputs

### 2.1 Symbols

| Symbol | Meaning | SI unit | Typical source (provenance) |
|---|---|---|---|
| N | Impeller rotational speed (revolutions per second) | 1/s | Batch `agitation_speed` (sensor) or scenario-derived (calculated) |
| D | Impeller diameter | m | Vessel parameter `impeller_diameter` (vendor_datasheet / manual_entry) |
| T | Vessel inner diameter | m | Vessel parameter `vessel_inner_diameter` |
| H_L | Liquid height at working volume | m | Vessel parameter `liquid_height_at_working_volume` (manual_entry) |
| V_w | Liquid working volume | m³ | Batch metadata/series (source); scenario target volume (target) |
| P | Power input to liquid | W | Measured `power_draw` (sensor) or F-PWR-001 (calculated, estimated) |
| N_p | Impeller power number (dimensionless) | — | Vendor datasheet or published correlation (estimated) |
| ρ | Liquid (broth) density | kg/m³ | Passport medium context or scenario assumption |
| μ | Liquid dynamic viscosity | Pa·s | Passport medium context or scenario assumption |
| Q_g | Volumetric gas flow rate | m³/s | Batch `airflow`/`gas_flow_total` (sensor) or scenario-derived |
| kLa | Volumetric oxygen mass-transfer coefficient | 1/s | Vessel kLa evidence (lab_assay / vendor_datasheet / published_correlation) |
| C* | Dissolved O₂ saturation concentration at process conditions | mol/m³ | Passport/scenario (lab_assay / published / user_assumption) |
| C_L | Actual dissolved O₂ concentration | mol/m³ | F-DOC-001 from DO % and C*, or `dissolved_oxygen_conc` sensor |
| DO | Dissolved oxygen, % of air saturation | % air sat | Batch `dissolved_oxygen` (sensor) or scenario constraint |

### 2.2 Unit pitfalls (must be unit-tested)
- **rpm → 1/s:** divide by 60. Never convert through radians (2π error in u_tip and Re).
- **vvm** is gas volume per liquid volume per **minute**; internal 1/s ×60 for display.
- **Gas flow reference conditions:** standard (e.g., SLPM) vs actual flow must be declared and consistent across scales (**OQ-032**). MVP does not convert between standard and actual conditions.
- **kLa** commonly reported in 1/h; internal 1/s.
- **P/V:** 1 W/L = 1 kW/m³.

### 2.3 Deriving source operating values from batches (PROPOSED, shown to user as assumptions)
| Input | Default statistic | User override |
|---|---|---|
| N (source) | Median of valid `agitation_speed` in selected window | p95, max, explicit value |
| Q_g (source) | Median of valid `airflow` (+`oxygen_flow` if user selects total) | p95, max, explicit |
| V_w (source) | Batch metadata working volume; else median of `working_volume` | explicit value |
| DO (source, for C_L) | Minimum valid `dissolved_oxygen` (also report p05) | median, explicit |
| OUR (source, for oxygen demand) | Max of user-supplied `our` series, if present | explicit |
| Multiple batches | Compute per batch; use the most demanding value (max N, max Q_g, min DO, max OUR) | per-batch selection (**OQ-025**) |

Window default = whole batch. For fed-batch, volume and demand change over time; the selected window must be shown in the report.

---

## 3. Oxygen transfer

### 3.1 F-OTR-001 — Oxygen transfer rate (CONFIRMED `[BP p.6]`)

$$
\mathrm{OTR} = k_La\,(C^* - C_L)
$$

| Variable | Unit (SI / display) |
|---|---|
| OTR | mol/(m³·s) / mmol/(L·h) |
| kLa | 1/s / 1/h |
| C*, C_L | mol/m³ / mmol/L |

**What it assesses:** oxygen-transfer capacity relative to the driving force between saturation and actual DO `[BP p.6]`.

**Evaluations performed (PROPOSED):**
1. *OTR at required DO* — C_L from the DO level the process must maintain (scenario constraint `min_do_required`, else passport `do_setpoint`); evaluated for source and target using each vessel's selected kLa evidence point.
2. *Theoretical upper bound at C_L = 0* — `OTR_max = kLa·C*`; labelled "upper bound at zero DO, not an operating condition".

**Assumptions (displayed):** liquid phase treated as well-mixed with single C_L; kLa and C* correspond to the same medium, temperature, pressure, gas composition and operating point; steady state.
**Limitations (CONFIRMED `[BP p.6]`):** "a relationship, not a complete prediction model". Credible assessment requires appropriate kLa and O₂ concentration data, consistent units and a process-relevant basis. Large vessels may have DO gradients (C_L not uniform) — not represented.
**Missing input behaviour:** any of kLa, C*, DO-required missing → `insufficient_evidence`.

### 3.2 F-DOC-001 — DO conversion (PROPOSED)

$$
C_L = \frac{DO_{\%}}{100}\,C^*
$$

Assumes the DO probe was calibrated to 100% at conditions equivalent to those defining C*. If calibration status is `unknown`, warning `DO_CALIBRATION_UNKNOWN` and rule R-DAT-004.

### 3.3 kLa evidence — F-KLA-000 (CONFIRMED descriptor `[BP p.6]`; handling PROPOSED)
kLa is **not calculated** in MVP. It is entered as **kLa evidence points** on a vessel version ([13](13_EQUIPMENT_COMPATIBILITY.md) §3.4): `{kla, N, Q_g, V_w, medium_description, temperature, method, provenance, value_nature, source_ref}`.
- The scenario selects one evidence point per vessel as representative.
- If the selected point's (N, Q_g, V_w) differ from the operating point being evaluated, the result carries warning `KLA_CONDITIONS_MISMATCH` listing the differences, and R-OXY-004 triggers. **No interpolation or extrapolation** in MVP (it would be a model requiring validation).
- kLa from `published_correlation` is accepted only with a citation and validity range in `source_ref`; flagged by R-OXY-004 as "correlation not validated for this vessel/medium" `[BP p.6]`.

---

## 4. Power and hydrodynamics

### 4.1 F-PV-001 — Power per volume (CONFIRMED `[BP p.6]`)

$$
\frac{P}{V} = \frac{P}{V_w}
$$

Units: P [W], V_w [m³] → W/m³ (display kW/m³). Assesses power-input intensity relevant to mixing, energy dissipation and hydrodynamics `[BP p.6]`.

**Source of P (priority order):** (1) measured `power_draw` series (sensor; note whether motor electrical power or shaft power — electrical power overstates power to liquid; user must declare, warning otherwise); (2) F-PWR-001 estimate (estimated). **Motor rated power is never used as P** — it is a capability limit used only in compatibility checks.

### 4.2 F-PWR-001 — Ungassed power from power number (PROPOSED, **OQ-012**)

$$
P_0 = N_p\,\rho\,N^3\,D^5
$$

| Variable | Unit |
|---|---|
| P₀ | W |
| N_p | dimensionless, impeller-specific |
| ρ | kg/m³ |
| N | 1/s |
| D | m |

**Assumptions:** N_p treated as constant, which holds approximately only in the fully turbulent regime for a given impeller geometry and vessel configuration (baffled); Newtonian liquid. **Multiple impellers:** total = Σ per impeller, assuming impellers are spaced far enough apart not to interact — assumption displayed; requires advisor confirmation.
**Limitations:** ungassed value; aeration generally reduces power draw relative to ungassed conditions by an amount depending on impeller type and gas flow — **no gassed correction is applied in MVP** (warning `UNGASSED_POWER_ESTIMATE`). N_p from vendor or literature must be cited; result `value_nature = estimated`.
**Rule link:** if Re at the same point is below the configured turbulent threshold, R-MIX-003 triggers and the P₀ result carries `VALIDITY_LIMIT_EXCEEDED`.

### 4.3 F-TIP-001 — Impeller tip speed (CONFIRMED `[BP p.6]`)

$$
u_{tip} = \pi\,N\,D
$$

u_tip [m/s], N [1/s], D [m]. Helps compare shear-related and hydrodynamic conditions `[BP p.6]`. For multiple impellers of different diameter, computed for the largest D (PROPOSED) with each listed in details.

### 4.4 F-RE-001 — Impeller Reynolds number (CONFIRMED `[BP p.6]`)

$$
Re = \frac{\rho\,N\,D^2}{\mu}
$$

Dimensionless. Flow-regime indicator `[BP p.6]`. **Assumption:** Newtonian broth with viscosity μ at process temperature. For non-Newtonian broths (e.g., high-biomass or filamentous cultures) an apparent viscosity model would be needed — out of scope; warning `NEWTONIAN_ASSUMPTION`. Regime classification thresholds are **configuration owned by the scientific lead** (**OQ-013**); the engine reports Re and the configured classification, or `not_configured`.

### 4.5 F-GEO-001 — Geometric ratios (PROPOSED)
D/T and H_L/T for each vessel, plus impeller count and type equality. Used by R-MIX-004 (geometric similarity) — derivations in §8 do **not** assume similarity, but similarity strongly affects whether matched descriptors imply similar hydrodynamics.

---

## 5. Aeration

### 5.1 F-VVM-001 — Gas flow per volume (CONFIRMED `[BP p.6]`)

$$
vvm = \frac{Q_g}{V_w}
$$

Q_g [m³/s], V_w [m³] → 1/s internally; display ×60 as vvm (1/min). Aeration intensity per unit liquid volume `[BP p.6]`.

### 5.2 F-VS-001 — Superficial gas velocity (PROPOSED)

$$
v_s = \frac{Q_g}{\pi T^2/4}
$$

v_s [m/s], T [m]. A gas-flow descriptor that, unlike vvm, increases with vessel size at constant vvm (because volume grows faster than cross-section). **Assumption:** Q_g evaluated at consistent conditions (**OQ-032**); actual gas volume changes with hydrostatic pressure in tall vessels — not corrected.

---

## 6. Thermal (inputs only in MVP)
The Blueprint requires thermal-capability risk warnings and lists heat balance, cooling capacity and temperature trends as needed evidence `[BP p.3, p.5]` but provides no equation. MVP:
- Target vessel parameter `cooling_capacity` [W] (provenance required).
- Scenario input `estimated_heat_load` [W] (user-supplied with provenance; method stated in note).
- Source batch temperature deviation from setpoint (max |T − T_set|) as a descriptive statistic.
No heat-generation correlation is computed (**OQ-015**).

## 7. Mixing (inputs only in MVP)
Mixing time is named in the Blueprint `[BP p.3, p.6]` without an equation. MVP accepts measured `mixing_time` per vessel (with method and conditions). No mixing-time correlation is computed (**OQ-010**).

---

## 8. Scale-up criteria and trade-off computation (PROPOSED)

### 8.1 Model
A scenario selects **agitation criteria** (S-PV, S-TIP; one primary) and **one aeration basis** (S-VVM or S-VS). Optionally S-KLA (evaluation-only). For each agitation criterion *c*:
1. Compute target N_t from *c*.
2. Compute target Q_g,t from the aeration basis.
3. Compute all descriptors (P/V, u_tip, Re, vvm, v_s, OTR) at (N_t, Q_g,t, V_t) for the target.
4. Report ratios `target / source` for every descriptor and status per descriptor.
5. Pass the operating point to the Equipment Compatibility Engine ([13](13_EQUIPMENT_COMPATIBILITY.md)).

This produces the side-by-side trade-off table required by `[BP p.4, p.6]` and makes explicit that preserving one descriptor changes the others.

### 8.2 Criterion equations

| ID | Preserves | Target equation | Required inputs | Notes |
|---|---|---|---|---|
| S-TIP | u_tip | N_t = N_s·D_s / D_t | N_s, D_s, D_t | Exact from F-TIP-001 |
| S-PV | P/V | N_t = [ (P/V)_s · V_t / (N_p,t · ρ · D_t⁵) ]^(1/3) | (P/V)_s, V_t, N_p,t, ρ, D_t | Uses F-PWR-001 at target; inherits its assumptions (turbulent, ungassed, constant N_p) |
| S-VVM | vvm | Q_g,t = vvm_s · V_t | vvm_s, V_t | Aeration basis |
| S-VS | v_s | Q_g,t = v_s,s · π·T_t²/4 | v_s,s, T_t | Aeration basis |
| S-KLA | kLa | **No derivation.** Compare selected target kLa evidence point (and its conditions) to source kLa | kLa evidence both vessels | `insufficient_evidence` if target kLa evidence absent (expected common case) |

### 8.3 Explanatory scaling under geometric similarity (for UI help text only)
With linear scale factor L = D_t/D_s, constant N_p, V ∝ D³, P ∝ N³D⁵:

| Held constant | N_t/N_s | (P/V) ratio | u_tip ratio | Re ratio |
|---|---|---|---|---|
| u_tip | L⁻¹ | L⁻¹ | 1 | L |
| P/V | L^(−2/3) | 1 | L^(1/3) | L^(4/3) |

and at constant vvm, v_s ratio = L. These are algebraic consequences of the equations above, provided to explain trade-offs; the engine always uses actual vessel geometry, not this table.

### 8.4 Process constraints
User constraints (e.g., `max_tip_speed`, `max_p_per_v`, `min_do_required`, `max_vvm`) are compared with the computed target values; violations become R-MIX-001 / R-OXY-001 flags. Constraint values are user-supplied with provenance — the engine never proposes them.

---

## 9. Test vectors (implementation arithmetic checks)

Inputs are test numbers chosen for easy hand calculation; **N_p = 5, C* = 0.20 mmol/L etc. are not recommended or validated property values.** Expected values must be independently recomputed (spreadsheet or hand) by Person 1 and stored in fixtures; tolerance `rel = 1e-6` unless stated.

| # | Formula | Inputs | Expected |
|---|---|---|---|
| T1 | unit | 60 rpm | 1.0 1/s |
| T2 | F-TIP-001 | N = 500 rpm (8.3333 1/s), D = 0.055 m | u_tip = 1.43990 m/s |
| T3 | F-RE-001 | ρ = 1000 kg/m³, N = 8.3333 1/s, D = 0.055 m, μ = 0.001 Pa·s | Re = 25 208.3 |
| T4 | F-VVM-001 | Q_g = 1 L/min, V_w = 2 L | 0.5 vvm |
| T5 | F-PV-001 | P = 10 W, V_w = 2 L | 5000 W/m³ (5 kW/m³) |
| T6 | F-PWR-001 | N_p = 5, ρ = 1000, N = 25/3 1/s, D = 0.055 m | P₀ = 1.45626 W |
| T7 | F-OTR-001 + F-DOC-001 | kLa = 100 1/h, C* = 0.20 mmol/L, DO = 30% | C_L = 0.06 mmol/L; OTR = 14.0 mmol/(L·h) |
| T8 | F-OTR-001 upper bound | kLa = 100 1/h, C* = 0.20 mmol/L | 20.0 mmol/(L·h) |
| T9 | F-VS-001 | Q_g = 1 L/min, T = 0.13 m | v_s = 1.2557 × 10⁻³ m/s (rel 1e-4) |
| T10 | S-TIP | N_s = 500 rpm, D_s = 0.055 m, D_t = 0.25 m | N_t = 110 rpm |
| T11 | S-PV | (P/V)_s from T6 at V_s = 2 L (728.13 W/m³), V_t = 150 L, N_p,t = 5, ρ = 1000, D_t = 0.25 m | N_t ≈ 2.818 1/s ≈ 169 rpm (rel 1e-3; exact value from independent check) |
| T12 | S-VVM | vvm_s = 0.5, V_t = 150 L | Q_g,t = 75 L/min |
| T13 | Missing input | F-RE-001 without μ | `insufficient_evidence`, missing_inputs = ["μ"] |
| T14 | Dimensional | Pass D in L | `UnitDimensionError` |

## 10. Validation requirements (CONFIRMED layers `[BP p.11]`)
1. **Software correctness:** T1–T14 + property tests (e.g., u_tip linear in N and D; Re scales with D²) + dimensional checks.
2. **Engineering correctness:** independent calculation review by a bioprocess engineer; comparison with trusted engineering references; each formula's `review_status` → `approved` only after this.
3. **Equipment realism:** vessel inputs checked against manufacturer specs and partner measurements.
4. **Process relevance:** compare outputs with actual batches/pilot observations; document where models do not generalize.
Until (2) is complete, every report states that calculations are pending expert review.
