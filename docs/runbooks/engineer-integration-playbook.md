# Engineer Integration Playbook (API + SDK)

Use this playbook for service-side integration with assignments and event ingestion.

## API-first flow

1. Fetch assignment

```bash
curl -s -X POST http://localhost:8000/api/v1/assignments \
  -H 'Content-Type: application/json' \
  -d '{"experiment_id":"<exp-id>","unit_id":"user-42","attributes":{"country":"US"}}'
```

2. Log exposure

```bash
curl -s -X POST http://localhost:8000/api/v1/events/exposure \
  -H 'Content-Type: application/json' \
  -d '{"experiment_id":"<exp-id>","unit_id":"user-42","variant_key":"control"}'
```

3. Log metric

```bash
curl -s -X POST http://localhost:8000/api/v1/events/metric \
  -H 'Content-Type: application/json' \
  -d '{"experiment_id":"<exp-id>","unit_id":"user-42","variant_key":"control","metric_name":"order_value","value":120.5}'
```

## Python SDK flow

Use `ExperimentClient` from `sdk/python` when you need retries, buffering, and fail-safe fallback.

```python
from litmus import ExperimentClient

client = ExperimentClient(base_url='http://localhost:8000', api_key='dev-token')
assignment = client.get_variant(experiment_id='exp-id', unit_id='user-42', attributes={'country': 'US'})
client.log_exposure('exp-id', 'user-42', assignment.variant_key)
client.log_metric('exp-id', 'user-42', assignment.variant_key, 'order_value', 120.5)
client.flush()
```

## Reliability notes
- Enable `ADMIN_API_TOKENS` in non-dev environments.
- Keep assignment and exposure logging tightly coupled.
- Use idempotent unit ids where possible to preserve deterministic assignment behavior.
- Treat `stop` as hard kill: fallback to control path in your service once stopped.
