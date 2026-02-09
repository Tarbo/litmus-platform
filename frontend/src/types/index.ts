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
  confidence: number;
  estimated_days_to_decision: number | null;
  diff_in_diff_delta: number | null;
  last_updated_at: string;
}
