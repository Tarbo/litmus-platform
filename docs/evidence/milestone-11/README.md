# Milestone 11 Evidence

## Commands run

1. Backend tests (strict warnings)
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/backend
./venv3.12/bin/pytest -q -W error::DeprecationWarning
```

2. SDK tests
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/sdk
../backend/venv3.12/bin/pytest -q python/tests
```

3. Frontend build
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/frontend
npm run build
```

## Artifacts
- `backend-pytest.txt`
- `sdk-pytest.txt`
- `frontend-build.txt`

## Feature evidence
- Added explicit exposure/metric ingestion contracts with single and batch support.
- Added `/events/exposure` and `/events/metric` endpoints while preserving legacy `/events` ingestion compatibility.
- Added `/results/{experiment_id}` endpoint returning exposure totals, exposure time series, metric summaries, and lift estimates with confidence intervals.
- Added backend integration tests validating event batching and results aggregation behavior.
