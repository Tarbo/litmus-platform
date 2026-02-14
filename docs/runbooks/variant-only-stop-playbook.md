# Variant-Only Setup + Controlled Stop Guide

Use this guide when you want to prepare variants without immediately launching traffic.

## Variant-only mode (no launch)

1. Create experiment in draft status (`POST /api/v1/experiments` or UI form).
2. Define variant keys, weights, and `config_json` values.
3. Validate:
- weights sum to `1.0`
- key naming is stable for integration
- targeting schema is valid
4. Do not call launch endpoint yet.

## Handoff checklist before launch
- Product confirms hypothesis and success metric.
- Engineering confirms assignment and event instrumentation.
- Analyst confirms readout plan and stop thresholds.

## Controlled stop while running

UI:
- Open `/experiments/{id}`.
- Click `Stop`.

API:

```bash
curl -s -X POST http://localhost:8000/api/v1/experiments/<exp-id>/stop \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <admin-token>' \
  -d '{"actor":"ops.oncall","reason":"guardrail breach"}'
```

Behavior after stop:
- Experiment status transitions to `stopped`.
- Relaunch is blocked by lifecycle rules.
- Integrations should default to control behavior.
