export type ExperimentStatus =
  | 'draft'
  | 'running'
  | 'passed'
  | 'failed'
  | 'inconclusive'
  | 'terminated_without_cause';

export interface CondensedPerformance {
  experiment_id: string;
  name: string;
  status: ExperimentStatus;
  exposures: number;
  conversions: number;
  conversion_rate: number;
  uplift_vs_control: number;
  confidence: number;
  sample_progress: number;
}

export interface ExecutiveSummary {
  passed: number;
  failed: number;
  running: number;
  inconclusive: number;
  terminated_without_cause: number;
}

export interface Variant {
  id?: string;
  name: string;
  traffic_allocation: number;
}

export interface Experiment {
  id: string;
  name: string;
  hypothesis: string;
  mde: number;
  baseline_rate: number;
  alpha: number;
  power: number;
  sample_size_required: number;
  status: ExperimentStatus;
  started_at: string | null;
  ended_at: string | null;
  termination_reason: string | null;
  variants: Variant[];
}

export interface ExperimentReport {
  experiment_id: string;
  status: ExperimentStatus;
  mde: number;
  sample_size_required: number;
  exposures: number;
  conversions: number;
  sample_progress: number;
  control_conversion_rate: number;
  treatment_conversion_rate: number;
  uplift_vs_control: number;
  uplift_ci_lower: number;
  uplift_ci_upper: number;
  p_value: number;
  confidence: number;
  recommendation: string;
  guardrails_breached: number;
  guardrails: Array<{
    name: string;
    value: number;
    threshold_value: number;
    direction: 'max' | 'min';
    status: 'healthy' | 'breached';
    observed_at: string;
  }>;
  estimated_days_to_decision: number | null;
  diff_in_diff_delta: number | null;
  assignment_policy: string;
  bandit_state: Array<{
    variant_id: string;
    variant_name: string;
    exposures: number;
    conversions: number;
    alpha: number;
    beta: number;
    expected_rate: number;
    win_probability: number;
  }>;
  variant_performance: Array<{
    variant_id: string;
    variant_name: string;
    post_exposures: number;
    post_conversions: number;
    post_conversion_rate: number;
    pre_exposures: number;
    pre_conversions: number;
    pre_conversion_rate: number;
  }>;
  last_updated_at: string;
}

export interface ReportSnapshot {
  id: string;
  experiment_id: string;
  snapshot: ExperimentReport;
  created_at: string;
}

export interface GuardrailMetric {
  id: string;
  experiment_id: string;
  name: string;
  value: number;
  threshold_value: number;
  direction: 'max' | 'min';
  status: 'healthy' | 'breached';
  observed_at: string;
}

export interface DecisionAudit {
  id: string;
  experiment_id: string;
  previous_status: string;
  new_status: string;
  reason: string | null;
  source: 'auto' | 'manual';
  actor: string;
  created_at: string;
}
