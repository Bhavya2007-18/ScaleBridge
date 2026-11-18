# 08 — API Specification

**Purpose:** Define the REST contract between frontend and backend. This contract is **frozen per week** (Monday lock `[BP p.12]`); changes require coordination between Person 3 (owner) and Person 4 (consumer).
**Related:** [07_DATABASE_SCHEMA.md](07_DATABASE_SCHEMA.md) · [09_DATA_INGESTION.md](09_DATA_INGESTION.md) · [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [17_SECURITY_AND_PRIVACY.md](17_SECURITY_AND_PRIVACY.md)

All items in this document are **PROPOSED** (the Blueprint specifies FastAPI + Pydantic and API validation `[BP p.10]` but no endpoints). The FastAPI-generated OpenAPI document is the machine-readable source; this file is the human-readable design and must be kept in sync.

---

## 1. Conventions
- Base path: `/api/v1`. JSON, UTF-8, `snake_case` fields.
- Auth: `Authorization: Bearer <access_token>`; refresh token in `httpOnly; Secure; SameSite=Strict` cookie.
- Organization context: header `X-Organization-Id: <uuid>` required on all tenant endpoints; server verifies membership.
- IDs: UUID strings. Timestamps: ISO 8601 UTC (`2026-11-18T10:00:00Z`).
- Pagination: `?limit=50&cursor=<opaque>` → `{ "items": [...], "next_cursor": "..." | null }`. Max limit 200.
- Quantities are always objects, never bare numbers:
```json
{ "value": 2.0, "unit": "L", "provenance": "vendor_datasheet", "value_nature": "measured", "source_ref": "Datasheet rev B p.3" }
```
- Responses from the scientific engine always include SI value and display value with units.
- Idempotency: `POST` that creates assessments/reports accepts optional `Idempotency-Key` header.

## 2. Error envelope
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable summary",
    "details": [{ "field": "target_working_volume.unit", "issue": "Unknown unit 'lt'" }],
    "request_id": "01JD…"
  }
}
```
| HTTP | code | When |
|---|---|---|
| 400 | `BAD_REQUEST` | Malformed request |
| 401 | `UNAUTHENTICATED` | Missing/expired token |
| 403 | `FORBIDDEN` | Role lacks permission / not member of org |
| 404 | `NOT_FOUND` | Missing **or belongs to another org** (never reveal existence) |
| 409 | `CONFLICT` | Duplicate name/run_code; editing locked scenario; immutable entity |
| 413 | `FILE_TOO_LARGE` | Upload over limit (**OQ-008**, default 50 MB) |
| 415 | `UNSUPPORTED_FILE_TYPE` | Not CSV/XLSX |
| 422 | `VALIDATION_ERROR` | Schema/unit validation failures |
| 422 | `INGESTION_ERROR` | Parse/mapping failure (details list rows/columns) |
| 500 | `INTERNAL_ERROR` | Unexpected; no stack traces in response |

> Note: `insufficient_evidence` is **not an error**. It is a normal 200/201 result value.

## 3. Endpoints

### 3.1 Auth & identity
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/auth/login` | public | `{email, password}` → `{access_token, expires_in, user}` + refresh cookie |
| POST | `/auth/refresh` | cookie | Rotate refresh, new access token |
| POST | `/auth/logout` | any | Revoke refresh token |
| POST | `/auth/accept-invite` | public | `{token, full_name, password}` |
| GET | `/me` | any | User + memberships `[{organization_id, name, role}]` |
| GET | `/organizations/{org_id}/members` | org_admin | List members |
| POST | `/organizations/{org_id}/invitations` | org_admin | `{email, role}` |
| PATCH | `/organizations/{org_id}/members/{user_id}` | org_admin | `{role}` |
| DELETE | `/organizations/{org_id}/members/{user_id}` | org_admin | Remove membership |

### 3.2 Projects & Process Passport
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects` | viewer+ | List |
| POST | `/projects` | scientist+ | Create |
| GET | `/projects/{id}` | viewer+ | Detail incl. latest passport version |
| PATCH | `/projects/{id}` | scientist+ | Name, product_family, organism_name, strain_metadata, process_type |
| POST | `/projects/{id}/archive` | org_admin | Archive |
| GET | `/projects/{id}/passport-versions` | viewer+ | List versions |
| POST | `/projects/{id}/passport-versions` | scientist+ | Create new immutable version |
| GET | `/projects/{id}/passport-versions/{version}` | viewer+ | One version |
| GET | `/projects/{id}/data-checklist` | viewer+ | Checklist (FR-PP-03) |

`POST /projects` request:
```json
{
  "name": "Protease P1 scale-up",
  "product_family": "industrial_enzyme",
  "organism_name": "Bacillus sp. (demo)",
  "strain_metadata": { "strain_id": "DEMO-001" },
  "process_type": "fed_batch",
  "is_synthetic_demo": true
}
```

`POST /projects/{id}/passport-versions` request:
```json
{
  "recipe_version": "R3",
  "process_description": "Aerobic fed-batch, glucose feed after batch phase",
  "medium_context": {
    "name": "Defined medium M9-mod",
    "density": { "value": 1020, "unit": "kg/m^3", "provenance": "user_assumption", "value_nature": "assumed" },
    "viscosity": null,
    "oxygen_saturation_concentration": null
  },
  "process_parameters": [
    { "key": "temperature_setpoint", "value": 37, "unit": "degC", "provenance": "manual_entry", "value_nature": "measured" },
    { "key": "do_setpoint", "value": 30, "unit": "percent_air_saturation", "provenance": "manual_entry", "value_nature": "measured" }
  ],
  "change_note": "Initial passport"
}
```

`GET /projects/{id}/data-checklist` response:
```json
{
  "items": [
    { "key": "medium.viscosity", "required_by": ["F-RE-001"], "status": "missing" },
    { "key": "medium.density", "required_by": ["F-RE-001","F-PWR-001"], "status": "assumed" },
    { "key": "target_vessel.kla", "required_by": ["F-OTR-001","S-KLA"], "status": "missing" }
  ],
  "summary": { "present": 12, "assumed": 3, "estimated": 1, "missing": 4 }
}
```

### 3.3 Files & ingestion — see [09](09_DATA_INGESTION.md)
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/projects/{id}/files` | scientist+ | multipart: `file`, `is_synthetic` (bool, required), `source_description` (required) → `DataFile` |
| GET | `/projects/{id}/files` | viewer+ | List |
| GET | `/files/{file_id}` | viewer+ | Metadata + status |
| GET | `/files/{file_id}/preview?sheet=&rows=50` | scientist+ | `{sheets, columns:[{name, inferred_type, sample_values}], rows}` |
| GET | `/mapping-templates` | scientist+ | Saved reusable mappings |
| PUT | `/files/{file_id}/mapping` | scientist+ | Mapping JSON ([09](09_DATA_INGESTION.md) §4); `save_as_template` optional |
| POST | `/files/{file_id}/dry-run` | scientist+ | Full validation → `QualityReport` (nothing committed) |
| POST | `/files/{file_id}/import` | scientist+ | `{batch: {...metadata}}` or `{batch_id}` → `{batch_id, measurement_count, sample_count, quality_report}` |
| GET | `/files/{file_id}/quality-report` | viewer+ | Last quality report |

`QualityReport`:
```json
{
  "file_id": "…",
  "rows_total": 4321,
  "rows_imported": 4310,
  "variables": [
    { "variable": "dissolved_oxygen", "unit_original": "%", "unit_si": "percent_air_saturation",
      "count": 4321, "missing": 11, "min_si": 4.2, "max_si": 100.0 }
  ],
  "issues": [
    { "check_code": "DQ-TS-GAP", "severity": "medium", "variable": null, "row_start": 1200, "row_end": 1201,
      "count": 1, "message": "Gap of 1800 s exceeds configured max gap of 300 s" }
  ],
  "conversions": [ { "variable": "agitation_speed", "from_unit": "rpm", "to_unit": "1/s", "method": "pint" } ],
  "blocking": false
}
```

### 3.4 Batches & measurements
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/batches` | viewer+ | List |
| GET | `/batches/{batch_id}` | viewer+ | Metadata + variable inventory |
| PATCH | `/batches/{batch_id}` | scientist+ | Metadata only (notes, operator, vessel_version_id, passport_version_id) |
| GET | `/batches/{batch_id}/measurements?variables=ph,dissolved_oxygen&from_s=&to_s=&max_points=2000` | viewer+ | Time series, downsampled server-side (LTTB, PROPOSED), returns `{variable, unit_display, points:[[elapsed_s, value, quality_flag]]}` |
| GET | `/batches/{batch_id}/samples` | viewer+ | Offline assays |
| GET | `/batches/{batch_id}/summary` | viewer+ | Derived summaries used by scenarios (min/max/mean per variable, with counts & quality) |

### 3.5 Vessels — see [13](13_EQUIPMENT_COMPATIBILITY.md)
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/vessels` | viewer+ | List (latest version summary) |
| POST | `/vessels` | scientist+ | Create vessel + version 1 |
| GET | `/vessels/{id}` | viewer+ | Latest version + parameters + `missing_specifications` |
| POST | `/vessels/{id}/versions` | scientist+ | New immutable version |
| GET | `/vessels/{id}/versions/{version}` | viewer+ | Specific version |
| GET | `/vessels/compare?a={version_id}&b={version_id}` | viewer+ | Side-by-side parameter table + derived geometric ratios |

`POST /vessels` request:
```json
{
  "name": "Lab-2L-A",
  "scale_class": "lab",
  "manufacturer": "ExampleCo",
  "model": "BT-2",
  "impeller_type": "rushton_turbine",
  "impeller_count": 2,
  "sparger_type": "ring",
  "instrumentation": ["ph_probe", "do_probe", "temperature_probe", "offgas_analyzer"],
  "controls": ["ph_control", "do_cascade_agitation", "temperature_control", "feed_pump"],
  "parameters": [
    { "key": "working_volume_max", "value": 2.0, "unit": "L", "provenance": "vendor_datasheet", "value_nature": "measured", "source_ref": "DS rev B" },
    { "key": "impeller_diameter", "value": 0.055, "unit": "m", "provenance": "manual_entry", "value_nature": "measured" },
    { "key": "agitation_speed_max", "value": 1200, "unit": "rpm", "provenance": "vendor_datasheet", "value_nature": "measured" }
  ],
  "change_note": "Initial profile"
}
```

### 3.6 Scenarios & assessments
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/projects/{id}/scenarios` | viewer+ | List |
| POST | `/projects/{id}/scenarios` | scientist+ | Create |
| GET | `/scenarios/{id}` | viewer+ | Detail |
| PATCH | `/scenarios/{id}` | scientist+ | Edit (409 if locked) |
| POST | `/scenarios/{id}/duplicate` | scientist+ | Copy (to edit after lock) |
| POST | `/scenarios/{id}/assessments` | scientist+ | Run → `Assessment` (201) |
| GET | `/scenarios/{id}/assessments` | viewer+ | List |
| GET | `/assessments/{id}` | viewer+ | Full assessment: summary, calculations, trade_offs, risk_flags, compatibility_checks, validation_tasks, reviews |
| PATCH | `/validation-tasks/{task_id}` | scientist+ | `{status, waived_reason?, assignee_user_id?}` |
| POST | `/assessments/{id}/reviews` | reviewer, org_admin | `{decision, comment}` |
| GET | `/science/formulas` | viewer+ | Formula registry (id, version, equation, variables, status, assumptions) |
| GET | `/science/criteria` | viewer+ | Available scale-up criteria |
| GET | `/science/rules` | viewer+ | Rule registry + active threshold config |
| GET | `/science/units` | viewer+ | Accepted units per variable |

`POST /projects/{id}/scenarios` request:
```json
{
  "name": "2 L → 200 L, constant P/V primary",
  "batch_ids": ["…", "…"],
  "source_vessel_version_id": "…",
  "target_vessel_version_id": "…",
  "target_working_volume": { "value": 150, "unit": "L", "provenance": "manual_entry", "value_nature": "assumed" },
  "criteria": [
    { "criterion_id": "S-PV", "is_primary": true },
    { "criterion_id": "S-TIP", "is_primary": false },
    { "criterion_id": "S-KLA", "is_primary": false }
  ],
  "aeration_basis": "S-VVM",
  "kla_selection": { "source_point_id": "kla-1", "target_point_id": null },
  "batch_window": null,
  "statistic_overrides": { "agitation_speed": "p95" },
  "constraints": [
    { "key": "max_tip_speed", "value": 5.0, "unit": "m/s", "provenance": "user_assumption", "value_nature": "assumed" },
    { "key": "min_do_required", "value": 20, "unit": "percent_air_saturation", "provenance": "user_assumption", "value_nature": "assumed" }
  ],
  "assumptions": [
    { "key": "medium.viscosity", "value": 0.001, "unit": "Pa*s", "provenance": "user_assumption", "value_nature": "assumed",
      "note": "Water-like viscosity assumed; not measured" }
  ]
}
```

`GET /assessments/{id}` response (abridged):
```json
{
  "id": "…",
  "scenario_id": "…",
  "status": "completed",
  "engine_version": "0.3.0",
  "formula_registry_version": "0.3.0",
  "rule_registry_version": "0.2.0",
  "is_synthetic": true,
  "summary": {
    "overall_evidence_level": "mixed",
    "flags": { "critical": 0, "high": 2, "medium": 3, "low": 1, "info": 2 },
    "insufficient_evidence_count": 3,
    "not_configured_count": 2
  },
  "calculations": [
    {
      "id": "…", "formula_id": "F-TIP-001", "formula_version": "1.0.0", "scale": "source", "criterion_id": null,
      "equation": "u_tip = π · N · D",
      "inputs": {
        "N": { "value": 8.333, "unit": "1/s", "display": "500 rpm", "provenance": "sensor", "value_nature": "measured" },
        "D": { "value": 0.055, "unit": "m", "provenance": "manual_entry", "value_nature": "measured" }
      },
      "output": { "value_si": 1.4399, "unit_si": "m/s", "display_value": 1.44, "display_unit": "m/s" },
      "value_nature": "calculated", "evidence_level": "measured", "status": "computed",
      "assumptions": ["N is the operating agitation speed taken as the median over the selected phase"],
      "warnings": []
    },
    {
      "formula_id": "F-OTR-001", "scale": "target", "status": "insufficient_evidence",
      "missing_inputs": ["kLa (target vessel)", "C* (oxygen saturation concentration)"],
      "output": null
    }
  ],
  "trade_offs": [
    { "criterion_id": "S-PV", "is_primary": true, "status": "computed",
      "target_operating_point": { "N": { "value": 2.9, "unit": "1/s" } },
      "descriptor_ratios": { "P_per_V": 1.0, "u_tip": 1.98, "Re": "…", "vvm": null } }
  ],
  "risk_flags": [ { "rule_id": "R-OXY-002", "severity": "high", "outcome": "insufficient_evidence", "title": "No kLa evidence for target vessel", "evidence_gap": "kLa measured in target vessel over the planned agitation/aeration range", "input_refs": [ { "kind": "vessel_parameter", "key": "kla" } ] } ],
  "compatibility_checks": [ { "check_id": "C-AGIT-RANGE", "criterion_id": "S-PV", "outcome": "compatible", "required_value_si": 2.9, "capability_min_si": 0.83, "capability_max_si": 6.67, "unit_si": "1/s" } ],
  "validation_tasks": [ { "task_code": "VT-KLA-TARGET", "task_type": "measurement", "priority": "P1", "status": "open", "title": "Measure kLa in target vessel", "linked_risk_flag_ids": ["…"] } ],
  "reviews": []
}
```
(Numbers above are illustrative of shape only.)

### 3.7 Reports
| Method | Path | Role | Description |
|---|---|---|---|
| POST | `/assessments/{id}/reports` | scientist+ | Generate new version → `Report` (201) |
| GET | `/assessments/{id}/reports` | viewer+ | List versions |
| GET | `/reports/{id}` | viewer+ | Metadata |
| GET | `/reports/{id}/download` | viewer+ | `application/pdf` stream; audit `report.downloaded` |

### 3.8 Audit
| Method | Path | Role | Description |
|---|---|---|---|
| GET | `/audit-events?entity_type=&entity_id=&actor=&from=&to=` | org_admin | Paginated |

### 3.9 Health
| GET | `/health/live` · `/health/ready` | public | Liveness; readiness checks DB + storage |

## 4. Contract change process
1. Proposer opens PR changing Pydantic schemas **and** this file.
2. Regenerate TS client; CI fails if client is stale.
3. Breaking change (remove/rename field, change semantics/units) requires Person 3 + Person 4 approval and is announced at Monday contract lock.
4. Science-output fields (`calculations`, `risk_flags`, …) additionally require Person 2 approval.

## 5. Acceptance criteria
- OpenAPI served at `/api/v1/openapi.json` matches this document (reviewed weekly).
- Contract tests: every endpoint has a test for 200/201, 401, 403 (wrong role), 404 (other org's resource).
