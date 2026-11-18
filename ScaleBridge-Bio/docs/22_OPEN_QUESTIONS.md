# 22 — Open Questions Register

**Purpose:** Track every domain, scientific, or commercial decision that requires founder or bioprocess advisor confirmation (`OPEN QUESTION`). Software modules must handle unresolved questions gracefully (e.g., via `not_configured` or `insufficient_evidence`) and never invent answers.
**Related:** [10_SCIENTIFIC_ENGINE.md](10_SCIENTIFIC_ENGINE.md) · [11_SCALE_UP_CALCULATIONS.md](11_SCALE_UP_CALCULATIONS.md) · [12_RISK_ENGINE.md](12_RISK_ENGINE.md)

---

| ID | Category | Question | Current software behavior until resolved | Owner |
|---|---|---|---|---|
| `OQ-001` | Product / Domain | Which single aerobic microbial process family (organism + product, e.g., *Bacillus* industrial protease fed-batch) is the official MVP wedge? | Supported as configurable Passport metadata; seeded demo clearly labeled `is_synthetic_demo = true`. | Person 1 |
| `OQ-002` | Data | Which real partner or published fermentation dataset will replace the synthetic hackathon dataset for incubation? | Ingestion supports any CSV/XLSX via column mapping; synthetic datasets enforce `is_synthetic = true`. | Person 1 |
| `OQ-007` | Infra | Which cloud provider (AWS Mumbai, GCP Mumbai, Azure Central India, or on-prem) is targeted for pilot hosting? | Containerized via Docker Compose; cloud-agnostic S3 + PostgreSQL interfaces. | Person 3 |
| `OQ-008` | Product | Maximum upload file size limit for CSV/XLSX batch files? | Configurable via `MAX_UPLOAD_MB` (default 50 MB). | Person 3 |
| `OQ-010` | Science | Should mixing time ($t_m$) correlations be added post-MVP, or remain measured-input-only? | Measured input only (`mixing_time_evidence`); `R-MIX-002` flags missing mixing evidence. | Person 1 + Advisor |
| `OQ-011` | Science | Are any published $k_La$ correlations (e.g., Van't Riet) approved for optional estimation in a specific vessel/medium class? | Excluded from MVP calculations; $k_La$ is entered as evidence points with provenance. | Person 1 + Advisor |
| `OQ-012` | Science | Reviewer sign-off on `F-PWR-001` ($P_0 = N_p \rho N^3 D^5$) and multi-impeller additivity assumption. | Marked `review_status = "pending_review"`; triggers `R-DAT-006` info flag until approved. | Person 1 + Advisor |
| `OQ-013` | Science | Numeric values for `ThresholdConfig` (`re_turbulent_min`, `descriptor_ratio_band`, `otr_demand_margin`, `cooling_margin`, `do_critical_percent`). | Default to `null` in engine baseline; scenarios allow explicit user-supplied thresholds with provenance `user_assumption`, otherwise rules return `not_configured`. | Person 1 + Advisor |
| `OQ-015` | Science | Should metabolic heat generation be estimated from OUR in a future version? | Out of MVP; user supplies `estimated_heat_load` with provenance or rule returns `insufficient_evidence`. | Person 1 |
| `OQ-016` | Science | Should OUR/CER be computed from raw off-gas $\mathrm{O_2/CO_2}$ analyzer data in a future release? | Out of MVP; `our` and `cer` are accepted as user-supplied time series or scenario inputs. | Person 1 + Person 2 |
| `OQ-021` | Security | Confirm final RBAC role names (`org_admin`, `scientist`, `reviewer`, `viewer`) and permissions. | Implemented as documented in `17_SECURITY_AND_PRIVACY.md`. | Person 3 + Person 4 |
| `OQ-022` | Privacy | Default data retention period and archival grace window for customer organizations? | Configurable `data_retention_days` per organization (`null` = retain until explicit deletion). | Person 3 |
| `OQ-023` | Product | Exact legal/operational wording for reviewer sign-off decisions? | `approved_for_discussion` and `changes_requested` with mandatory comment and non-warranty disclaimer. | Person 1 + Person 4 |
| `OQ-024` | Data | Minimum mandatory variables for a batch to be scenario-eligible? | Checked in Data Checklist; missing variables surface as `insufficient_evidence` per formula. | Person 1 + Person 2 |
| `OQ-032` | Science | Standard gas temperature/pressure reference conditions for `SLPM` conversions? | Mapping requires user note when `SLPM` is selected; treated as volumetric flow with warning if reference conditions unspecified. | Person 1 |
