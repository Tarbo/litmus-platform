export type ExperimentStatus = 'draft' | 'running' | 'paused' | 'stopped' | 'DRAFT' | 'RUNNING' | 'PAUSED' | 'STOPPED'

export interface Variant {
  id?: string
  key: string
  name: string
  weight: number
  config_json: Record<string, unknown>
}

export interface Experiment {
  id: string
  name: string
  description: string
  owner_team: string
  created_by: string
  tags: string[]
  unit_type: string
  targeting: Record<string, unknown>
  ramp_pct: number
  version: number
  status: ExperimentStatus
  sample_size_required: number
  variants: Variant[]
}

export interface CondensedPerformance {
  experiment_id: string
  name: string
  status: ExperimentStatus
  exposures: number
  conversions: number
  conversion_rate: number
  uplift_vs_control: number
  confidence: number
  sample_progress: number
}

export interface GuardrailMetric {
  id: string
  experiment_id: string
  name: string
  value: number
  threshold_value: number
  direction: string
  status: string
  observed_at: string
}

export interface ExperimentReport {
  experiment_id: string
  status: ExperimentStatus
  mde: number
  sample_size_required: number
  exposures: number
  conversions: number
  sample_progress: number
  control_conversion_rate: number
  treatment_conversion_rate: number
  uplift_vs_control: number
  uplift_ci_lower: number
  uplift_ci_upper: number
  p_value: number
  confidence: number
  recommendation: string
  guardrails_breached: number
  guardrails: Array<Record<string, unknown>>
  estimated_days_to_decision: number | null
  diff_in_diff_delta: number | null
  variant_performance: Array<Record<string, unknown>>
  assignment_policy: string
  bandit_state: Array<{
    variant_id: string
    variant_name: string
    exposures: number
    conversions: number
    alpha: number
    beta: number
    expected_rate: number
    win_probability: number
  }>
  last_updated_at: string
}

export interface ExperimentCreatePayload {
  name: string
  description: string
  owner_team: string
  created_by: string
  tags: string[]
  unit_type: string
  targeting: Record<string, unknown>
  ramp_pct: number
  variants: Variant[]
}

export interface ExperimentResultsResponse {
  experiment_id: string
  generated_at: string
  exposure_totals: Record<string, number>
  exposure_timeseries: Array<{
    variant_key: string
    variant_name: string
    points: Array<{ bucket_start: string; exposures: number }>
  }>
  metric_summaries: Array<{
    variant_key: string
    variant_name: string
    metric_name: string
    count: number
    mean: number
  }>
  lift_estimates: Array<{
    variant_key: string
    variant_name: string
    control_rate: number
    treatment_rate: number
    absolute_lift: number
    ci_lower: number
    ci_upper: number
    p_value: number
  }>
}
