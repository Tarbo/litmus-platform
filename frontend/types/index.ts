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
