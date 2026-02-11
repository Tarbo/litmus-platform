# API Contract (Self-Serve MVP)

Base path: `/api/v1`

Auth model:
- Read endpoints are open by default.
- Write endpoints require `Authorization: Bearer <token>` when `ADMIN_API_TOKENS` is configured.
- In `ENVIRONMENT=development` with empty `ADMIN_API_TOKENS`, write endpoints allow local testing.

Error model:
- Validation failures: `422` with FastAPI validation detail.
- Unauthorized writes: `401` with `{"detail":"Unauthorized write access"}`.
- Not found: `404` with `{"detail":"Experiment not found"}` (or resource-specific detail).
- Invalid lifecycle transition/contract: `400` with specific detail.

## Experiments

### `POST /experiments`
Create draft experiment.

Request (example):
```json
{
  "name": "Suggested Order v4",
  "description": "Compare control model with treatment model",
  "owner_team": "pricing-ds",
  "created_by": "owner.user",
  "tags": ["pricing", "model-v4"],
  "unit_type": "store_id",
  "targeting": {"country": {"in": ["US", "CA"]}},
  "ramp_pct": 10,
  "variants": [
    {"key": "control", "name": "Control", "weight": 0.5, "config_json": {"model": "v3"}},
    {"key": "treatment", "name": "Treatment", "weight": 0.5, "config_json": {"model": "v4"}}
  ]
}
```

Response: `200` `ExperimentResponse`.

### `GET /experiments`
List experiments.

Response: `200` array of `ExperimentResponse`.

### `GET /experiments/{id}`
Get single experiment.

Response: `200` `ExperimentResponse`.

### `PATCH /experiments/{id}`
Patch editable fields (`name`, `description`, `owner_team`, `tags`, `targeting`, `ramp_pct`, `variants`).

Response: `200` `ExperimentResponse`.

### `POST /experiments/{id}/launch`
Start or ramp running experiment.

Request:
```json
{"ramp_pct": 10, "actor": "ui.operator"}
```

Response: `200` `ExperimentResponse`.

### `POST /experiments/{id}/pause`
Pause running experiment.

Request:
```json
{"actor": "ui.operator"}
```

Response: `200` `ExperimentResponse`.

### `POST /experiments/{id}/stop`
Stop experiment (kill-switch behavior).

Request:
```json
{"actor": "ui.operator", "reason": "guardrail breach"}
```

Response: `200` `ExperimentResponse`.

## Assignments

### `POST /assignments`
Get deterministic assignment for `(experiment_id, unit_id, attributes)`.

Request:
```json
{
  "experiment_id": "exp_123",
  "unit_id": "store_42",
  "attributes": {"country": "US", "segment": "premium"}
}
```

Response:
```json
{
  "experiment_id": "exp_123",
  "assignment_id": "asg_abc",
  "unit_id": "store_42",
  "variant_key": "treatment",
  "config_json": {"model": "v4"},
  "experiment_version": 3
}
```

Compatibility endpoint: `POST /assignments/assign` (same contract).

## Events

### `POST /events/exposure`
Ingest single exposure event or array of exposure events.

Single request:
```json
{
  "experiment_id": "exp_123",
  "unit_id": "store_42",
  "variant_key": "treatment",
  "ts": "2026-02-11T12:00:00Z",
  "context": {"source": "sdk"}
}
```

Batch request:
```json
[
  {"experiment_id": "exp_123", "unit_id": "u1", "variant_key": "control"},
  {"experiment_id": "exp_123", "unit_id": "u2", "variant_key": "treatment"}
]
```

Response:
```json
{"ingested": 2}
```

### `POST /events/metric`
Ingest single metric event or array of metric events.

Single request:
```json
{
  "experiment_id": "exp_123",
  "unit_id": "store_42",
  "variant_key": "treatment",
  "metric_name": "order_value",
  "value": 1250.3,
  "ts": "2026-02-11T12:00:05Z",
  "context": {"source": "sdk"}
}
```

Response:
```json
{"ingested": 1}
```

## Results

### `GET /results/{experiment_id}?interval=hour|minute`
Return dashboard-ready aggregates:
- `exposure_totals`
- `exposure_timeseries`
- `metric_summaries`
- `lift_estimates`

Response: `200` `ExperimentResultsResponse`.

## Operational endpoints

- `GET /health` returns service liveness.
- `GET /ready` returns dependency readiness (database check).
- `GET /metrics` returns in-memory request counters and status-code distributions.
