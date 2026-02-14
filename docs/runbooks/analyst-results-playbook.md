# Analyst Results & Decisioning Playbook

Use this playbook to evaluate whether an experiment should continue, pause, or stop.

## Primary data views
- UI results page: `/experiments/{id}/results`
- API aggregates: `GET /api/v1/results/{id}?interval=minute`
- Analysis report: `GET /api/v1/experiments/{id}/report`

## Decision workflow

1. Confirm data health
- Exposure totals are increasing.
- Metric summaries have non-zero counts.
- No abnormal ingestion drops in `/metrics`.

2. Compare treatment vs control
- Read `absolute_lift`, CI bounds, and p-value from lift estimates.
- Validate directional consistency over multiple refresh windows.

3. Inspect bandit diagnostics
- In report payload, inspect `bandit_state`:
  - `expected_rate`
  - `win_probability`
  - `exposures` / `conversions`

4. Recommend action
- Continue if uncertainty is still high.
- Pause if quality/guardrail concerns appear.
- Stop when confidence and business constraints justify final decision.

## Evidence capture
- Save JSON export via `GET /api/v1/experiments/{id}/export?format=json`.
- Save CSV export via `GET /api/v1/experiments/{id}/export?format=csv`.
- Attach snapshots and rationale to milestone issue/decision log.
