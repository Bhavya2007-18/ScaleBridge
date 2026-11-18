# 13 — Equipment Compatibility Engine

**Purpose:** Specify vessel profile parameters, controlled vocabularies, missing-specification detection, and capability-envelope compatibility checks (`C-*`).
**Related:** [07_DATABASE_SCHEMA.md](07_DATABASE_SCHEMA.md) §4.3 · [08_API_SPECIFICATION.md](08_API_SPECIFICATION.md) §3.5 · [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md) · [12_RISK_ENGINE.md](12_RISK_ENGINE.md) §4.5

---

## 1. Requirements (CONFIRMED `[BP p.4, p.5, p.11]`)
- Enter lab and target vessel geometry, impellers, working volume, motors and gas capabilities.
- Produce comparable equipment profiles and **missing-specification warnings**.
- Check whether a target vessel's documented capability envelope can support the process requirements.
- **Acceptance test:** two vessels can be saved and compared; every equipment risk flag links to a specific input, rule and evidence gap.

## 2. Design (PROPOSED)
Implemented as pure functions in `scalebridge_science/readiness/compatibility.py` and persisted in `compatibility_checks`. Evaluates each scenario agitation criterion's required operating point against the target vessel's documented envelope.

Outcomes (`compat_outcome`):
- `compatible`: required value lies within `[min, max]` (or `≤ max` for upper-only limits).
- `incompatible`: required value violates documented capability limit → triggers corresponding `R-EQP-*` flag ([12](12_RISK_ENGINE.md) §4.5).
- `cannot_evaluate`: either the required value could not be computed (`insufficient_evidence`) or the vessel capability parameter is missing → triggers `R-EQP-006`.

## 3. Vessel profile schema (PROPOSED)

### 3.1 Categorical attributes on `vessel_versions`
| Field | Controlled values |
|---|---|
| `scale_class` | `lab`, `pilot`, `production`, `other` |
| `impeller_type` | `rushton_turbine`, `pitched_blade_turbine`, `marine_propeller`, `hydrofoil`, `elephant_ear`, `other` |
| `impeller_count` | positive integer |
| `sparger_type` | `ring`, `open_pipe`, `microsparger`, `sintered`, `none`, `other` |

### 3.2 Numeric parameter keys (`vessel_parameters.key`)
All stored with original value/unit, SI value/unit, `provenance`, `value_nature` and optional `source_reference`.

| Key | Description | SI unit | Display | Required by |
|---|---|---|---|---|
| `total_volume` | Total vessel volume | m³ | L | — (descriptive) |
| `working_volume_min` | Minimum operable liquid volume | m³ | L | `C-VOLUME-RANGE` |
| `working_volume_max` | Maximum operable liquid volume | m³ | L | `C-VOLUME-RANGE` |
| `vessel_inner_diameter` | Inner tank diameter $T$ | m | mm | `F-VS-001`, `F-GEO-001` |
| `vessel_height` | Total straight-side height | m | mm | — |
| `liquid_height_at_working_volume` | Liquid height $H_L$ at nominal working volume | m | mm | `F-GEO-001` |
| `impeller_diameter` | Characteristic impeller diameter $D$ | m | mm | `F-TIP-001`, `F-RE-001`, `F-PWR-001`, `F-GEO-001` |
| `impeller_power_number` | Ungassed power number $N_p$ | dimensionless | — | `F-PWR-001`, `S-PV` |
| `agitation_speed_min` | Minimum agitation speed | 1/s | rpm | `C-AGIT-RANGE` |
| `agitation_speed_max` | Maximum agitation speed | 1/s | rpm | `C-AGIT-RANGE` |
| `motor_power_limit` | Rated motor/shaft power available to broth | W | kW | `C-MOTOR-POWER` |
| `gas_flow_min` | Minimum controllable sparger gas flow | m³/s | L/min | `C-GAS-RANGE` |
| `gas_flow_max` | Maximum controllable sparger gas flow | m³/s | L/min | `C-GAS-RANGE` |
| `max_headspace_pressure` | Max allowable operating pressure (absolute) | Pa | bar(a) | `C-PRESSURE` |
| `cooling_capacity` | Maximum heat removal rate at process temp | W | kW | `C-COOLING`, `R-THM-001/002` |
| `temperature_min` | Min controllable temperature | K | °C | `C-TEMP-RANGE` |
| `temperature_max` | Max controllable temperature | K | °C | `C-TEMP-RANGE` |

### 3.3 Instrumentation & controls vocabulary
`instrumentation`: `ph_probe`, `do_probe`, `temperature_probe`, `level_sensor`, `foam_probe`, `pressure_sensor`, `offgas_analyzer`, `balance_feed`, `torque_power_sensor`.
`controls`: `ph_control`, `do_cascade_agitation`, `do_cascade_airflow`, `do_cascade_o2`, `temperature_control`, `feed_pump`, `antifoam_pump`, `backpressure_control`.

### 3.4 kLa and mixing-time evidence (`vessel_versions.kla_evidence`, `mixing_time_evidence`)
```json
{
  "id": "kla-1",
  "kla": { "value": 0.0278, "unit": "1/s", "original_value": 100, "original_unit": "1/h",
           "provenance": "vendor_datasheet", "value_nature": "measured", "source_ref": "Factory test" },
  "agitation_speed": { "value": 8.333, "unit": "1/s", "original_value": 500, "original_unit": "rpm",
                       "provenance": "vendor_datasheet", "value_nature": "measured" },
  "gas_flow": { "value": 3.33e-5, "unit": "m^3/s", "original_value": 2.0, "original_unit": "L/min",
                "provenance": "vendor_datasheet", "value_nature": "measured" },
  "working_volume": { "value": 0.002, "unit": "m^3", "original_value": 2.0, "original_unit": "L",
                      "provenance": "vendor_datasheet", "value_nature": "measured" },
  "medium_description": "Deionized water, 37 °C",
  "method": "Dynamic gassing-out"
}
```

### 3.5 Missing-specification warnings (`GET /vessels/{id}`)
Computed whenever a vessel version is read: checks presence of `working_volume_min`, `working_volume_max`, `vessel_inner_diameter`, `impeller_diameter`, `impeller_power_number`, `agitation_speed_min`, `agitation_speed_max`, `motor_power_limit`, `gas_flow_min`, `gas_flow_max`, `cooling_capacity`, and at least one `kla_evidence` entry. Returns `missing_specifications: [{key, required_by_formulas, required_by_checks}]`.

## 4. Compatibility checks (`C-*`)

| Check ID | Per criterion? | Parameter(s) | Requirement source | Compatible condition | Linked rule |
|---|---|---|---|---|---|
| `C-VOLUME-RANGE` | No | `working_volume_min/max` | Scenario `target_working_volume` $V_t$ | $V_{min} \le V_t \le V_{max}$ | `R-EQP-004` |
| `C-AGIT-RANGE` | Yes | `agitation_speed_min/max` | Required target $N_t$ from criterion | $N_{min} \le N_t \le N_{max}$ | `R-EQP-001` |
| `C-MOTOR-POWER` | Yes | `motor_power_limit` | Target ungassed power $P_{0,t}$ at $N_t$ | $P_{0,t} \le P_{motor,max}$ | `R-EQP-002` |
| `C-GAS-RANGE` | No (per aeration basis) | `gas_flow_min/max` | Target $Q_{g,t}$ from `S-VVM` / `S-VS` | $Q_{g,min} \le Q_{g,t} \le Q_{g,max}$ | `R-EQP-003` |
| `C-COOLING` | No | `cooling_capacity` | Scenario `estimated_heat_load` | $Q_{heat} \le Q_{cool,max}$ | `R-THM-001/002` |
| `C-TEMP-RANGE` | No | `temperature_min/max` | Passport `temperature_setpoint` | $T_{min} \le T_{set} \le T_{max}$ | `R-EQP-006` |
| `C-INSTRUMENT` | No | `instrumentation`, `controls` | Required instruments/controls derived from passport (e.g., fed-batch requires `feed_pump`; DO setpoint requires `do_probe`) | All required items present in target | `R-EQP-005` |

## 5. Acceptance criteria
- Missing-spec warnings list every missing parameter from §3.5 with its downstream formulas/checks.
- Every `C-*` check has unit tests for `compatible`, `incompatible`, and `cannot_evaluate`.
- `GET /vessels/compare` returns side-by-side parameters in display units plus $D/T$ and $H_L/T$ for both vessels.
