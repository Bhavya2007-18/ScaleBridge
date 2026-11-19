export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  organism: string;
  target_molecule: string;
  expression_system?: string;
  created_at: string;
}

export interface Vessel {
  id: string;
  name: string;
  facility?: string;
  scale_category: 'lab' | 'pilot' | 'production';
  working_volume_min_l: number;
  working_volume_max_l: number;
  total_volume_l: number;
  aspect_ratio?: number;
  impeller_count: number;
  impeller_types: string[];
  baffle_count: number;
  sparger_type?: string;
  max_rpm?: number;
  max_power_w?: number;
  max_gassing_vvm?: number;
}

export interface Scenario {
  id: string;
  project_id: string;
  source_vessel_id: string;
  target_vessel_id: string;
  target_working_volume_l: number;
  selected_criteria: string[];
  target_process_temperature_c: number;
  operating_parameters?: Record<string, any>;
  notes?: string;
}

export interface CalculationResult {
  id: string;
  criterion_name: string;
  output_parameter: string;
  value_numeric?: number;
  value_unit?: string;
  provenance_classification: 'measured' | 'calculated' | 'estimated' | 'assumed';
  assumptions: string[];
  confidence_score?: number;
  insufficient_evidence: boolean;
  evidence_notes?: string;
}

export interface RiskFlag {
  id: string;
  category: string;
  title: string;
  description: string;
  severity: 'critical' | 'warning' | 'info';
  mitigation_suggestion?: string;
}

export interface CompatibilityCheck {
  id: string;
  item_category: string;
  parameter_name: string;
  required_value?: number;
  available_value?: number;
  unit?: string;
  status: 'compatible' | 'incompatible' | 'marginal';
  gap_analysis?: string;
}

export interface ValidationTask {
  id: string;
  phase: string;
  task_name: string;
  description: string;
  success_criteria: string;
  risk_addressed?: string;
  is_completed: boolean;
}

export interface Assessment {
  id: string;
  scenario_id: string;
  overall_readiness_score: number;
  status: string;
  summary_markdown?: string;
  calculations: CalculationResult[];
  risks: RiskFlag[];
  compatibility_checks: CompatibilityCheck[];
  validation_tasks: ValidationTask[];
  created_at: string;
}
