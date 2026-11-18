# Project Context — ScaleBridge Bio

**Read first before writing or modifying any code.**

## 1. What ScaleBridge Bio is
A vendor-agnostic, process-aware decision-support platform that compares laboratory-scale microbial fermentation data with target pilot/manufacturing vessel capabilities, computes deterministic scale-up engineering descriptors, surfaces criterion trade-offs and missing evidence, evaluates equipment compatibility and risks, creates a prioritized validation plan, and exports an auditable PDF Process-Transfer Report.

## 2. Core MVP modules
1. **Identity & Organizations (`identity`):** Multi-tenant isolation (`organization_id`), JWT auth, RBAC (`org_admin`, `scientist`, `reviewer`, `viewer`).
2. **Process Passport (`projects`):** Versioned record of organism, product family, process type (`batch`/`fed_batch`), recipe version, medium properties ($\rho, \mu, C^*$), process parameters, and automated Data Checklist.
3. **Data Ingestion (`ingestion`):** CSV/XLSX upload, raw file preservation (SHA-256), column mapping, Pint unit normalization, data-quality checks (`DQ-*`), and batch creation.
4. **Process Dashboard (`batches`):** Time-series inspection (pH, DO, temperature, RPM, airflow, feed, biomass/OD, titre) and multi-batch overlay comparison.
5. **Vessel Profiles (`vessels`):** Versioned lab and target bioreactor geometry, impellers, working volume limits, motor/agitation/aeration/cooling capabilities, instrumentation, $k_La$ evidence points, missing-spec warnings, and side-by-side comparison.
6. **Scientific Calculation Engine (`scalebridge_science`):** Pure, deterministic Python package computing `F-OTR-001` ($OTR = k_La(C^* - C_L)$), `F-DOC-001`, `F-PV-001` ($P/V$), `F-PWR-001` ($P_0 = N_p\rho N^3 D^5$), `F-TIP-001` ($u_{tip} = \pi ND$), `F-RE-001` ($Re = \rho ND^2/\mu$), `F-VVM-001` ($vvm = Q_g/V_w$), `F-VS-001` ($v_s$), `F-GEO-001` ($D/T, H_L/T$), and scale-up criteria trade-offs (`S-PV`, `S-TIP`, `S-VVM`, `S-VS`, `S-KLA`).
7. **Readiness Engine (`readiness`):**
   - **Equipment Compatibility Engine:** Checks target operating point against vessel capability envelope (`C-*`).
   - **Scale-up Risk Engine:** Rule-based warnings (`R-OXY-*`, `R-MIX-*`, `R-THM-*`, `R-DAT-*`, `R-EQP-*`) linking every flag to specific inputs, rules, and evidence gaps.
   - **Validation Planner:** Prioritized `P1`/`P2`/`P3` tasks (`VT-*`) and human reviewer sign-off (`review_signoffs`).
8. **Transfer Report (`reports`):** Versioned PDF report generation with full traceability, limitations, and synthetic-data watermarks.

## 3. Non-negotiable boundaries
- Never fabricate scientific equations, measurements, or silent default values.
- Missing inputs must return `insufficient_evidence` listing the exact missing parameters.
- Separate `measured`, `estimated`, `assumed`, and `calculated` values everywhere.
- Never implement live bioreactor control, setpoint writing, unvalidated ML/digital twins, or 21 CFR Part 11 claims.
