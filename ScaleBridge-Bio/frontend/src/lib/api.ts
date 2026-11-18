/**
 * Typed API contracts and HTTP client for ScaleBridge Bio `/api/v1` (docs/08_API_SPECIFICATION.md).
 */

export type Provenance =
  | "sensor"
  | "manual_entry"
  | "lab_assay"
  | "vendor_datasheet"
  | "published_correlation"
  | "user_assumption"
  | "calculated";

export type ValueNature = "measured" | "estimated" | "assumed" | "calculated";
export type EvidenceLevel = "measured" | "mixed" | "estimated" | "assumed" | "insufficient";
export type Severity = "critical" | "high" | "medium" | "low" | "info";
export type RuleOutcome = "triggered" | "not_triggered" | "insufficient_evidence" | "not_configured";
export type CompatOutcome = "compatible" | "incompatible" | "cannot_evaluate";

export interface Quantity {
  value: number;
  unit: string;
  original_value?: number | null;
  original_unit?: string | null;
  display_value?: number | null;
  display_unit?: string | null;
  provenance: Provenance;
  value_nature: ValueNature;
  source_ref?: string | null;
  note?: string | null;
}

export interface OrgMembership {
  organization_id: string;
  name: string;
  slug: string;
  role: string;
}

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  memberships: OrgMembership[];
}

export interface PassportVersion {
  id: string;
  project_id: string;
  version: number;
  recipe_version: string;
  process_description: string | null;
  organism_context: Record<string, unknown>;
  medium_context: {
    name?: string;
    density?: Quantity | null;
    viscosity?: Quantity | null;
    oxygen_saturation_concentration?: Quantity | null;
  };
  process_parameters: Array<{
    key: string;
    value: number;
    unit: string;
    provenance: Provenance;
    value_nature: ValueNature;
    note?: string;
  }>;
  material_context: Record<string, unknown>;
  change_note: string | null;
  created_by: string;
  created_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  name: string;
  product_family: string | null;
  organism_name: string | null;
  strain_metadata: Record<string, unknown>;
  process_type: string;
  owner_user_id: string;
  is_synthetic_demo: boolean;
  batch_count: number;
  scenario_count: number;
  latest_passport: PassportVersion | null;
  created_at: string;
  updated_at: string;
}

export interface DataChecklistItem {
  key: string;
  label: string;
  required_by: string[];
  status: string;
}

export interface DataChecklistResponse {
  items: DataChecklistItem[];
  summary: Record<string, number>;
}

export interface QualityIssue {
  check_code: string;
  severity: Severity;
  variable: string | null;
  row_start: number | null;
  row_end: number | null;
  count: number;
  message: string;
}

export interface QualityReport {
  file_id: string;
  rows_total: number;
  rows_imported: number;
  variables: Array<{
    variable: string;
    unit_original: string;
    unit_si: string;
    unit_display: string;
    count: number;
    valid_count: number;
    missing_count: number;
    invalid_count: number;
    min_display: number | null;
    max_display: number | null;
  }>;
  issues: QualityIssue[];
  conversions: Array<{
    variable: string;
    from_unit: string;
    to_unit: string;
    method: string;
    pint_version: string;
  }>;
  blocking: boolean;
}

export interface BatchRecord {
  id: string;
  project_id: string;
  run_code: string;
  scale_label: string | null;
  working_volume_original: number | null;
  working_volume_unit: string | null;
  working_volume_si: number | null;
  start_time: string | null;
  end_time: string | null;
  operator: string | null;
  notes: string | null;
  is_synthetic: boolean;
  variables_available: string[];
  summary: Record<
    string,
    {
      variable: string;
      unit_display: string;
      count_valid: number;
      min_display: number | null;
      median_display: number | null;
      max_display: number | null;
    }
  >;
  created_at: string;
}

export interface MeasurementSeries {
  variable: string;
  unit_display: string;
  unit_si: string;
  points: Array<{
    elapsed_s: number;
    elapsed_h: number;
    value: number | null;
    value_si: number | null;
    quality_flag: string;
  }>;
}

export interface VesselRecord {
  id: string;
  name: string;
  scale_class: "lab" | "pilot" | "production" | "other";
  manufacturer: string | null;
  model: string | null;
  location: string | null;
  latest_version: {
    id: string;
    version: number;
    impeller_type: string | null;
    impeller_count: number | null;
    sparger_type: string | null;
    instrumentation: string[];
    controls: string[];
    parameters: Record<string, Quantity>;
    kla_evidence: Array<{
      id: string;
      kla: Quantity;
      agitation_speed?: Quantity | null;
      gas_flow?: Quantity | null;
      working_volume?: Quantity | null;
      medium_description?: string | null;
      method?: string | null;
    }>;
    mixing_time_evidence: Array<{
      id: string;
      mixing_time: Quantity;
      method?: string | null;
    }>;
    change_note: string | null;
    created_at: string;
  };
  missing_specifications: Array<{
    key: string;
    required_by_formulas: string[];
    required_by_checks: string[];
  }>;
  created_at: string;
}

export interface CalculationResult {
  id: string;
  formula_id: string;
  formula_name: string;
  formula_version: string;
  review_status: string;
  scale: "source" | "target";
  criterion_id: string | null;
  equation: string;
  inputs: Record<string, Quantity>;
  output: Quantity | null;
  status: "computed" | "insufficient_evidence" | "not_applicable" | "error";
  missing_inputs: string[];
  evidence_level: EvidenceLevel;
  assumptions: string[];
  warnings: string[];
}

export interface TradeOffRow {
  criterion_id: string;
  criterion_name: string;
  is_primary: boolean;
  status: string;
  missing_inputs: string[];
  target_operating_point: Record<string, Quantity>;
  descriptors_target: Record<string, Quantity | null>;
  descriptor_ratios: Record<string, number | null>;
  assumptions: string[];
  warnings: string[];
}

export interface CompatibilityCheck {
  id: string;
  check_id: string;
  criterion_id: string | null;
  parameter_key: string;
  title: string;
  required_display: number | null;
  capability_min_display: number | null;
  capability_max_display: number | null;
  display_unit: string;
  outcome: CompatOutcome;
  explanation: string;
}

export interface RiskFlag {
  id: string;
  rule_id: string;
  rule_version: string;
  category: string;
  severity: Severity;
  outcome: RuleOutcome;
  title: string;
  explanation: string;
  input_refs: Array<{ kind: string; ref_id?: string | null; key: string }>;
  evidence_gap: string | null;
  validation_task_codes: string[];
}

export interface ValidationTask {
  id: string;
  task_code: string;
  task_type: string;
  title: string;
  description: string;
  priority: "P1" | "P2" | "P3";
  status: "open" | "in_progress" | "done" | "waived";
  waived_reason: string | null;
  updated_at: string;
}

export interface AssessmentRecord {
  id: string;
  scenario_id: string;
  status: string;
  engine_version: string;
  formula_registry_version: string;
  rule_registry_version: string;
  is_synthetic: boolean;
  summary: {
    overall_evidence_level: EvidenceLevel;
    triggered_by_severity: Record<string, number>;
    insufficient_evidence_flag_count: number;
    not_configured_flag_count: number;
    incompatible_check_count: number;
    cannot_evaluate_check_count: number;
    validation_task_count: number;
  };
  calculations: CalculationResult[];
  trade_offs: TradeOffRow[];
  compatibility_checks: CompatibilityCheck[];
  risk_flags: RiskFlag[];
  validation_tasks: ValidationTask[];
  reviews: Array<{
    id: string;
    reviewer_name: string;
    decision: string;
    comment: string;
    created_at: string;
  }>;
  reports: Array<{
    id: string;
    version: number;
    sha256: string;
    size_bytes: number;
    generated_at: string;
  }>;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

export function getStoredAuth(): { token: string | null; orgId: string | null; user: UserProfile | null } {
  if (typeof window === "undefined") {
    return { token: null, orgId: null, user: null };
  }
  const token = window.localStorage.getItem("sb_token");
  const orgId = window.localStorage.getItem("sb_org_id");
  const rawUser = window.localStorage.getItem("sb_user");
  const user = rawUser ? (JSON.parse(rawUser) as UserProfile) : null;
  return { token, orgId, user };
}

export function setStoredAuth(token: string, orgId: string, user: UserProfile): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("sb_token", token);
  window.localStorage.setItem("sb_org_id", orgId);
  window.localStorage.setItem("sb_user", JSON.stringify(user));
}

export function clearStoredAuth(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("sb_token");
  window.localStorage.removeItem("sb_org_id");
  window.localStorage.removeItem("sb_user");
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const { token, orgId } = getStoredAuth();
  const headers = new Headers(options.headers || {});
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (orgId) {
    headers.set("X-Organization-Id", orgId);
  }
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMessage = `HTTP ${res.status}`;
    try {
      const errBody = await res.json();
      errMessage = errBody?.detail?.error?.message || errBody?.detail || errMessage;
    } catch {
      // ignore json parse error
    }
    throw new Error(errMessage);
  }

  return (await res.json()) as T;
}

export function getReportDownloadUrl(reportId: string): string {
  return `${API_BASE}/reports/${reportId}/download`;
}
