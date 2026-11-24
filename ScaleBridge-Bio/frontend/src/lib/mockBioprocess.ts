import type {
  AssessmentRecord,
  BatchRecord,
  DataChecklistResponse,
  Project,
  VesselRecord,
} from "@/lib/api";

export type DataOrigin = "live" | "simulated" | "sample";

export interface BioprocessTimePoint {
  hour: number;
  temperatureC: number;
  ph: number;
  dissolvedOxygenPct: number;
  agitationRpm: number;
  biomassGL: number;
  glucoseGL: number;
  titerGL: number;
  efficiencyPct: number;
}

export interface ScaleUpPreviewInput {
  sourceVolumeL: number;
  sourceRpm: number;
  sourceImpellerM: number;
  targetVolumeL: number;
  targetRpm: number;
  targetImpellerM: number;
  aerationVvm: number;
  densityKgM3?: number;
  viscosityPaS?: number;
  powerNumber?: number;
}

export interface ScaleUpPreviewResult {
  sourcePvWm3: number;
  targetPvWm3: number;
  sourceTipSpeedMs: number;
  targetTipSpeedMs: number;
  targetReynolds: number;
  regime: "turbulent" | "transitional" | "laminar";
  targetKlaPerH: number;
  targetPowerW: number;
  vvm: number;
  shearStatus: "nominal" | "watch" | "critical";
  massTransferStatus: "nominal" | "watch" | "critical";
}

export interface AiOptimizationInsight {
  id: string;
  title: string;
  category: "mass_transfer" | "shear" | "metabolism" | "thermal";
  confidencePct: number;
  impactLabel: string;
  rationale: string;
  recommendedAction: string;
  dataOrigin: DataOrigin;
}

export const SAMPLE_BIOPROCESS_SERIES: BioprocessTimePoint[] = [
  { hour: 0, temperatureC: 36.8, ph: 7.12, dissolvedOxygenPct: 98.2, agitationRpm: 140, biomassGL: 0.45, glucoseGL: 24.0, titerGL: 0.02, efficiencyPct: 78 },
  { hour: 12, temperatureC: 36.8, ph: 7.10, dissolvedOxygenPct: 84.5, agitationRpm: 155, biomassGL: 1.35, glucoseGL: 21.8, titerGL: 0.14, efficiencyPct: 81 },
  { hour: 24, temperatureC: 36.8, ph: 7.08, dissolvedOxygenPct: 68.4, agitationRpm: 175, biomassGL: 3.40, glucoseGL: 17.6, titerGL: 0.42, efficiencyPct: 85 },
  { hour: 36, temperatureC: 36.9, ph: 7.05, dissolvedOxygenPct: 52.0, agitationRpm: 195, biomassGL: 6.80, glucoseGL: 12.4, titerGL: 0.96, efficiencyPct: 89 },
  { hour: 48, temperatureC: 36.8, ph: 7.03, dissolvedOxygenPct: 43.2, agitationRpm: 210, biomassGL: 10.90, glucoseGL: 8.1, titerGL: 1.64, efficiencyPct: 92 },
  { hour: 60, temperatureC: 36.8, ph: 7.02, dissolvedOxygenPct: 40.5, agitationRpm: 215, biomassGL: 14.20, glucoseGL: 11.5, titerGL: 2.38, efficiencyPct: 94 },
  { hour: 72, temperatureC: 36.7, ph: 7.01, dissolvedOxygenPct: 39.8, agitationRpm: 220, biomassGL: 16.40, glucoseGL: 9.2, titerGL: 3.12, efficiencyPct: 95 },
  { hour: 84, temperatureC: 36.8, ph: 7.02, dissolvedOxygenPct: 40.1, agitationRpm: 215, biomassGL: 17.30, glucoseGL: 6.8, titerGL: 3.74, efficiencyPct: 94 },
  { hour: 96, temperatureC: 36.8, ph: 7.04, dissolvedOxygenPct: 41.6, agitationRpm: 205, biomassGL: 17.10, glucoseGL: 4.5, titerGL: 4.18, efficiencyPct: 93 },
  { hour: 108, temperatureC: 36.8, ph: 7.06, dissolvedOxygenPct: 44.0, agitationRpm: 195, biomassGL: 16.60, glucoseGL: 3.1, titerGL: 4.46, efficiencyPct: 91 },
  { hour: 120, temperatureC: 36.8, ph: 7.08, dissolvedOxygenPct: 47.5, agitationRpm: 185, biomassGL: 15.90, glucoseGL: 2.2, titerGL: 4.62, efficiencyPct: 90 },
];

export function computeScaleUpPreview(input: ScaleUpPreviewInput): ScaleUpPreviewResult {
  const rho = input.densityKgM3 ?? 1020;
  const mu = input.viscosityPaS ?? 0.0014;
  const np = input.powerNumber ?? 2.4;
  const gassedFactor = 0.85;

  const srcVolM3 = Math.max(0.0001, input.sourceVolumeL / 1000);
  const tgtVolM3 = Math.max(0.001, input.targetVolumeL / 1000);

  const srcN = input.sourceRpm / 60;
  const tgtN = input.targetRpm / 60;

  const srcPowerW = np * rho * Math.pow(srcN, 3) * Math.pow(input.sourceImpellerM, 5) * gassedFactor;
  const targetPowerW = np * rho * Math.pow(tgtN, 3) * Math.pow(input.targetImpellerM, 5) * gassedFactor;

  const sourcePvWm3 = srcPowerW / srcVolM3;
  const targetPvWm3 = targetPowerW / tgtVolM3;

  const sourceTipSpeedMs = Math.PI * srcN * input.sourceImpellerM;
  const targetTipSpeedMs = Math.PI * tgtN * input.targetImpellerM;

  const targetReynolds = (rho * tgtN * Math.pow(input.targetImpellerM, 2)) / mu;
  const regime: "turbulent" | "transitional" | "laminar" =
    targetReynolds >= 10000 ? "turbulent" : targetReynolds >= 10 ? "transitional" : "laminar";

  // Tank diameter approximated as D_impeller / 0.35
  const tankDiameterM = input.targetImpellerM / 0.35;
  const crossSectionM2 = Math.PI * Math.pow(tankDiameterM / 2, 2);
  const gasFlowM3S = (input.aerationVvm * input.targetVolumeL) / 60000;
  const superficialVelMs = Math.max(0.0005, gasFlowM3S / Math.max(0.001, crossSectionM2));

  // Van't Riet correlation kLa (s^-1) -> (1/h)
  const klaSec = 0.026 * Math.pow(Math.max(1, targetPvWm3), 0.4) * Math.pow(superficialVelMs, 0.5);
  const targetKlaPerH = klaSec * 3600;

  const shearStatus =
    targetTipSpeedMs > 2.6 ? "critical" : targetTipSpeedMs > 2.1 ? "watch" : "nominal";
  const massTransferStatus =
    targetKlaPerH < 22 ? "critical" : targetKlaPerH < 32 ? "watch" : "nominal";

  return {
    sourcePvWm3,
    targetPvWm3,
    sourceTipSpeedMs,
    targetTipSpeedMs,
    targetReynolds,
    regime,
    targetKlaPerH,
    targetPowerW,
    vvm: input.aerationVvm,
    shearStatus,
    massTransferStatus,
  };
}

export const SAMPLE_AI_INSIGHTS: AiOptimizationInsight[] = [
  {
    id: "ai-1",
    title: "O₂ Cascade Optimization for Late Exponential Phase",
    category: "mass_transfer",
    confidencePct: 94,
    impactLabel: "+11.4% OTR Headroom",
    rationale:
      "Predicted oxygen uptake rate peaks at 64–78 h. Shifting primary DO cascade toward pure O₂ trim above 195 RPM preserves kLa without elevating impeller tip shear.",
    recommendedAction: "Cap agitation at 210 RPM and initiate 15% O₂ enrichment ramp at VCD > 12×10⁶ cells/mL.",
    dataOrigin: "simulated",
  },
  {
    id: "ai-2",
    title: "Impeller Tip Speed Margin vs. CHO Viability",
    category: "shear",
    confidencePct: 91,
    impactLabel: "-18% Hydrodynamic Stress",
    rationale:
      "At 200 L pilot geometry (D = 0.28 m), matching exact lab P/V drives tip speed near 2.15 m/s. Switching to pitched-blade hydrofoil reduces peak Kolmogorov eddy dissipation.",
    recommendedAction: "Target 120–145 W/m³ P/V band and confirm LDH baseline during pilot water run.",
    dataOrigin: "simulated",
  },
  {
    id: "ai-3",
    title: "Glucose Bolus Synchronization",
    category: "metabolism",
    confidencePct: 88,
    impactLabel: "+0.42 g/L Titer Gain",
    rationale:
      "Residual glucose drops below 3.5 g/L at 96 h while lactate re-assimilation stabilizes. Continuous micro-feed stabilizes specific productivity q_p.",
    recommendedAction: "Schedule 4.2 g/L/day exponential feed profile from hour 48 to 108.",
    dataOrigin: "sample",
  },
];

export const SAMPLE_PROJECTS: Project[] = [
  {
    id: "proj_demo_mab104",
    organization_id: "org_mock_demo_01",
    name: "mAb-104 Fed-Batch CHO-K1 Tech Transfer",
    product_family: "IgG1 Monoclonal Antibody",
    organism_name: "CHO-K1 Suspension",
    strain_metadata: { clone: "SB-CHO-4088", doubling_time_h: 21.4 },
    process_type: "Fed-Batch Aerobic",
    owner_user_id: "usr_mock_demo_01",
    is_synthetic_demo: true,
    batch_count: 3,
    scenario_count: 2,
    latest_passport: {
      id: "pass_v3",
      project_id: "proj_demo_mab104",
      version: 3,
      recipe_version: "R-2026.2",
      process_description:
        "High-density mammalian fed-batch fermentation transferring from 2 L glass benchtop to 150 L single-use pilot vessel.",
      organism_context: { host: "CHO-K1", shear_limit_m_s: 2.2 },
      medium_context: {
        name: "Chemically Defined CD-CHO + Glucose/Glutamine Feed",
        density: {
          value: 1025,
          unit: "kg/m^3",
          provenance: "user_assumption",
          value_nature: "assumed",
        },
        viscosity: {
          value: 1.4,
          unit: "mPa*s",
          provenance: "user_assumption",
          value_nature: "assumed",
        },
        oxygen_saturation_concentration: {
          value: 0.21,
          unit: "mmol/L",
          provenance: "published_correlation",
          value_nature: "estimated",
        },
      },
      process_parameters: [
        { key: "temperature_setpoint", value: 36.8, unit: "degC", provenance: "sensor", value_nature: "measured" },
        { key: "ph_setpoint", value: 7.05, unit: "pH", provenance: "sensor", value_nature: "measured" },
        { key: "do_setpoint", value: 40.0, unit: "%sat", provenance: "sensor", value_nature: "measured" },
        { key: "target_pv", value: 120.0, unit: "W/m^3", provenance: "calculated", value_nature: "calculated" },
      ],
      material_context: {},
      change_note: "Validated hydrodynamic envelope for 150 L SUB transfer",
      created_by: "Dr. Elena Vance",
      created_at: "2026-11-20T09:30:00Z",
    },
    created_at: "2026-11-01T10:00:00Z",
    updated_at: "2026-11-20T09:30:00Z",
  },
];

export const SAMPLE_CHECKLIST: DataChecklistResponse = {
  items: [
    { key: "working_volume", label: "Working Volume Bounds", required_by: ["F-PV-01", "F-VVM-01"], status: "complete" },
    { key: "impeller_diameter", label: "Impeller Diameter & Np", required_by: ["F-TIP-01", "F-RE-01"], status: "complete" },
    { key: "broth_rheology", label: "Broth Density & Viscosity", required_by: ["F-RE-01", "F-KLA-01"], status: "assumed" },
    { key: "target_kla", label: "Measured Target Vessel kLa", required_by: ["R-OTR-02"], status: "missing" },
  ],
  summary: { complete: 2, assumed: 1, missing: 1 },
};

export const SAMPLE_BATCHES: BatchRecord[] = [
  {
    id: "batch_lab_01",
    project_id: "proj_demo_mab104",
    run_code: "LAB-2L-RUN-01",
    scale_label: "2 L Benchtop",
    working_volume_original: 2.0,
    working_volume_unit: "L",
    working_volume_si: 0.002,
    start_time: "2026-10-12T08:00:00Z",
    end_time: "2026-10-17T08:00:00Z",
    operator: "Dr. Elena Vance",
    notes: "Baseline reference golden batch",
    is_synthetic: true,
    variables_available: ["temperature", "ph", "dissolved_oxygen", "agitation_rpm", "biomass", "glucose", "titer"],
    summary: {
      titer: { variable: "titer", unit_display: "g/L", count_valid: 11, min_display: 0.02, median_display: 2.38, max_display: 4.62 },
    },
    created_at: "2026-10-17T08:30:00Z",
  },
  {
    id: "batch_lab_02",
    project_id: "proj_demo_mab104",
    run_code: "LAB-2L-RUN-02",
    scale_label: "2 L Benchtop",
    working_volume_original: 2.0,
    working_volume_unit: "L",
    working_volume_si: 0.002,
    start_time: "2026-10-25T08:00:00Z",
    end_time: "2026-10-30T08:00:00Z",
    operator: "M. Chen",
    notes: "High-agitation stress verification run",
    is_synthetic: true,
    variables_available: ["temperature", "ph", "dissolved_oxygen", "agitation_rpm", "biomass", "glucose", "titer"],
    summary: {
      titer: { variable: "titer", unit_display: "g/L", count_valid: 11, min_display: 0.02, median_display: 2.15, max_display: 4.35 },
    },
    created_at: "2026-10-30T09:00:00Z",
  },
];

export const SAMPLE_VESSELS: VesselRecord[] = [
  {
    id: "ves_lab_2l",
    name: "Biostat B-DCU 2L Glass",
    scale_class: "lab",
    manufacturer: "Sartorius",
    model: "UniVessel 2L",
    location: "R&D Upstream Suite B",
    latest_version: {
      id: "vv_lab_2l",
      version: 2,
      impeller_type: "2x 3-Blade Segment / Pitched",
      impeller_count: 2,
      sparger_type: "Micro-sparger ring",
      instrumentation: ["pH", "dO2 Optical", "PT100", "Off-gas O2/CO2"],
      controls: ["Cascade Agitation + O2", "Dual Acid/Base"],
      parameters: {
        working_volume_max: { value: 2.0, unit: "L", provenance: "vendor_datasheet", value_nature: "measured" },
        impeller_diameter: { value: 0.055, unit: "m", provenance: "vendor_datasheet", value_nature: "measured" },
        max_agitation_speed: { value: 800, unit: "rpm", provenance: "vendor_datasheet", value_nature: "measured" },
        max_power: { value: 250, unit: "W", provenance: "vendor_datasheet", value_nature: "measured" },
        max_aeration: { value: 2.0, unit: "vvm", provenance: "vendor_datasheet", value_nature: "measured" },
      },
      kla_evidence: [],
      mixing_time_evidence: [],
      change_note: "Verified mechanical geometry",
      created_at: "2026-10-01T12:00:00Z",
    },
    missing_specifications: [],
    created_at: "2026-10-01T12:00:00Z",
  },
  {
    id: "ves_pilot_150l",
    name: "HyPerforma 150L Single-Use Pilot",
    scale_class: "pilot",
    manufacturer: "Thermo Fisher",
    model: "S.U.B. 150",
    location: "Pilot Facility Wing 2",
    latest_version: {
      id: "vv_pilot_150l",
      version: 1,
      impeller_type: "Pitched-Blade Hydrofoil",
      impeller_count: 1,
      sparger_type: "Drilled-Hole + Frit Microsparger",
      instrumentation: ["pH", "dO2", "Load Cell", "Exhaust Condenser"],
      controls: ["4-Gas MFC Mixer", "Jacket Chiller Loop"],
      parameters: {
        working_volume_max: { value: 150.0, unit: "L", provenance: "vendor_datasheet", value_nature: "measured" },
        impeller_diameter: { value: 0.24, unit: "m", provenance: "vendor_datasheet", value_nature: "measured" },
        max_agitation_speed: { value: 240, unit: "rpm", provenance: "vendor_datasheet", value_nature: "measured" },
        max_power: { value: 2200, unit: "W", provenance: "vendor_datasheet", value_nature: "measured" },
        max_aeration: { value: 1.0, unit: "vvm", provenance: "vendor_datasheet", value_nature: "measured" },
      },
      kla_evidence: [],
      mixing_time_evidence: [],
      change_note: "Pilot commissioning baseline",
      created_at: "2026-10-05T12:00:00Z",
    },
    missing_specifications: [
      {
        key: "measured_broth_kla",
        required_by_formulas: ["F-OTR-02"],
        required_by_checks: ["C-O2-01"],
      },
    ],
    created_at: "2026-10-05T12:00:00Z",
  },
  {
    id: "ves_prod_2000l",
    name: "BioFlo Pro 2000L Stainless GMP",
    scale_class: "production",
    manufacturer: "Eppendorf",
    model: "BioFlo Pro 2000",
    location: "GMP Manufacturing Bay 4",
    latest_version: {
      id: "vv_prod_2000l",
      version: 1,
      impeller_type: "Dual Rushton + Marine Hybrid",
      impeller_count: 3,
      sparger_type: "Ring Sparger",
      instrumentation: ["Redundant pH", "Redundant dO2", "Mass Spec Off-gas"],
      controls: ["DeltaV DCS Loop", "Chilled Glycol Jacket"],
      parameters: {
        working_volume_max: { value: 2000.0, unit: "L", provenance: "vendor_datasheet", value_nature: "measured" },
        impeller_diameter: { value: 0.56, unit: "m", provenance: "vendor_datasheet", value_nature: "measured" },
        max_agitation_speed: { value: 165, unit: "rpm", provenance: "vendor_datasheet", value_nature: "measured" },
        max_power: { value: 11000, unit: "W", provenance: "vendor_datasheet", value_nature: "measured" },
        max_aeration: { value: 0.8, unit: "vvm", provenance: "vendor_datasheet", value_nature: "measured" },
      },
      kla_evidence: [],
      mixing_time_evidence: [],
      change_note: "GMP qualification profile",
      created_at: "2026-10-08T12:00:00Z",
    },
    missing_specifications: [],
    created_at: "2026-10-08T12:00:00Z",
  },
];

export const SAMPLE_ASSESSMENT: AssessmentRecord = {
  id: "assess_demo_01",
  scenario_id: "scen_demo_01",
  status: "completed",
  engine_version: "1.4.0",
  formula_registry_version: "2026.11",
  rule_registry_version: "2026.11",
  is_synthetic: true,
  summary: {
    overall_evidence_level: "mixed",
    triggered_by_severity: { critical: 0, high: 1, medium: 2, low: 0, info: 1 },
    insufficient_evidence_flag_count: 1,
    not_configured_flag_count: 0,
    incompatible_check_count: 0,
    cannot_evaluate_check_count: 1,
    validation_task_count: 4,
  },
  calculations: [
    {
      id: "calc_pv",
      formula_id: "F-PV-01",
      formula_name: "Aerated Specific Power Input (P/V)",
      formula_version: "1.2",
      review_status: "verified",
      scale: "target",
      criterion_id: "S-PV",
      equation: "P/V = (Np · ρ · N³ · D⁵ · fg) / V",
      inputs: {
        N: { value: 145, unit: "rpm", provenance: "calculated", value_nature: "calculated" },
        D: { value: 0.24, unit: "m", provenance: "vendor_datasheet", value_nature: "measured" },
        V: { value: 150, unit: "L", provenance: "user_assumption", value_nature: "assumed" },
      },
      output: { value: 124.8, unit: "W/m^3", provenance: "calculated", value_nature: "calculated" },
      status: "computed",
      missing_inputs: [],
      evidence_level: "mixed",
      assumptions: ["Np = 2.4 for pitched-blade hydrofoil", "Aerated factor fg = 0.85"],
      warnings: [],
    },
    {
      id: "calc_tip",
      formula_id: "F-TIP-01",
      formula_name: "Impeller Tip Speed (v_tip)",
      formula_version: "1.0",
      review_status: "verified",
      scale: "target",
      criterion_id: "S-TIP",
      equation: "v_tip = π · N · D",
      inputs: {
        N: { value: 145, unit: "rpm", provenance: "calculated", value_nature: "calculated" },
        D: { value: 0.24, unit: "m", provenance: "vendor_datasheet", value_nature: "measured" },
      },
      output: { value: 1.822, unit: "m/s", provenance: "calculated", value_nature: "calculated" },
      status: "computed",
      missing_inputs: [],
      evidence_level: "measured",
      assumptions: ["Synchronous VFD drive speed"],
      warnings: [],
    },
    {
      id: "calc_kla",
      formula_id: "F-KLA-01",
      formula_name: "Volumetric Mass Transfer Coefficient (kLa)",
      formula_version: "1.1",
      review_status: "pending_review",
      scale: "target",
      criterion_id: "S-VVM",
      equation: "kLa = α · (P/V)^β · (v_s)^γ",
      inputs: {
        PV: { value: 124.8, unit: "W/m^3", provenance: "calculated", value_nature: "calculated" },
        v_s: { value: 0.0042, unit: "m/s", provenance: "calculated", value_nature: "calculated" },
      },
      output: { value: 36.4, unit: "1/h", provenance: "published_correlation", value_nature: "estimated" },
      status: "computed",
      missing_inputs: [],
      evidence_level: "estimated",
      assumptions: ["Van't Riet air-water coalescing correlation (α=0.026, β=0.4, γ=0.5)"],
      warnings: ["Antifoam surfactant may reduce empirical kLa by 15–25% in CHO broth."],
    },
  ],
  trade_offs: [],
  compatibility_checks: [
    {
      id: "cmp_motor",
      check_id: "C-PWR-01",
      criterion_id: "S-PV",
      parameter_key: "agitation_power",
      title: "Motor Drive Shaft Power Headroom",
      required_display: 18.7,
      capability_min_display: 15,
      capability_max_display: 2200,
      display_unit: "W",
      outcome: "compatible",
      explanation: "Required shaft power (18.7 W) is safely within 2,200 W pilot drive ceiling.",
    },
    {
      id: "cmp_rpm",
      check_id: "C-RPM-01",
      criterion_id: "S-PV",
      parameter_key: "agitation_rpm",
      title: "Impeller Rotational Speed Envelope",
      required_display: 145,
      capability_min_display: 25,
      capability_max_display: 240,
      display_unit: "rpm",
      outcome: "compatible",
      explanation: "Target 145 RPM operates in optimal VFD torque band (25–240 RPM).",
    },
    {
      id: "cmp_cooling",
      check_id: "C-THM-01",
      criterion_id: null,
      parameter_key: "jacket_cooling",
      title: "Peak Metabolic Heat Removal Capacity",
      required_display: null,
      capability_min_display: null,
      capability_max_display: null,
      display_unit: "kW",
      outcome: "cannot_evaluate",
      explanation: "Missing pilot chilled-glycol U·A heat transfer coefficient from facility datasheet.",
    },
  ],
  risk_flags: [
    {
      id: "rf_kla",
      rule_id: "R-OTR-02",
      rule_version: "1.0",
      category: "mass_transfer",
      severity: "high",
      outcome: "triggered",
      title: "Antifoam Suppression Risk on Predicted kLa",
      explanation:
        "Empirical air-water kLa (36.4 1/h) does not account for Pluronic F-68 and antifoam coalescence changes during peak exponential oxygen demand.",
      input_refs: [{ kind: "calculation", ref_id: "calc_kla", key: "kLa" }],
      evidence_gap: "Measured kLa in actual CD-CHO production medium at 150 L scale.",
      validation_task_codes: ["VAL-KLA-01"],
    },
    {
      id: "rf_mix",
      rule_id: "R-MIX-01",
      rule_version: "1.0",
      category: "mixing",
      severity: "medium",
      outcome: "triggered",
      title: "pH / Base Addition Micro-Zone Gradient",
      explanation:
        "Scaling 2 L → 150 L increases circulation mixing time (~14 s vs 2.5 s). Top-mounted alkali dosing risks transient local pH spikes near feed plume.",
      input_refs: [],
      evidence_gap: null,
      validation_task_codes: ["VAL-MIX-01"],
    },
    {
      id: "rf_therm",
      rule_id: "R-THM-01",
      rule_version: "1.0",
      category: "thermal",
      severity: "medium",
      outcome: "insufficient_evidence",
      title: "Insufficient Evidence: Jacket Thermal Transfer Coefficient",
      explanation: "Facility heat-exchange curve for 150 L SUB jacket has not been uploaded.",
      input_refs: [],
      evidence_gap: "Upload chiller loop ΔT specification.",
      validation_task_codes: ["VAL-THM-01"],
    },
  ],
  validation_tasks: [
    {
      id: "vt_1",
      task_code: "VAL-KLA-01",
      task_type: "pilot_qualification",
      title: "Dynamic Gassing-Out kLa Determination in CD-CHO Matrix",
      description: "Measure clean broth kLa with 0.1% Pluronic F-68 at 145 RPM and 0.6 VVM prior to GMP seed transfer.",
      priority: "P1",
      status: "open",
      waived_reason: null,
      updated_at: "2026-11-20T09:30:00Z",
    },
    {
      id: "vt_2",
      task_code: "VAL-MIX-01",
      task_type: "hydrodynamic",
      title: "95% Blend Mixing Time Conductivity Probe Check",
      description: "Verify mixing time τ_95 < 18 s via KCl pulse injection during cold water commissioning run.",
      priority: "P2",
      status: "in_progress",
      waived_reason: null,
      updated_at: "2026-11-20T09:30:00Z",
    },
    {
      id: "vt_3",
      task_code: "VAL-THM-01",
      task_type: "facility_fit",
      title: "Confirm Chilled Glycol Jacket U·A Thermal Margin",
      description: "Obtain pilot engineering U·A curve to verify ΔT thermal safety margin at 18.5×10⁶ cells/mL.",
      priority: "P2",
      status: "open",
      waived_reason: null,
      updated_at: "2026-11-20T09:30:00Z",
    },
  ],
  reviews: [],
  reports: [],
  created_at: "2026-11-20T09:35:00Z",
};
