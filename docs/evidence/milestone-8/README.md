# Milestone 8 Evidence

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
- Added backend startup preflight database connectivity check in app lifespan.
- Added `/ready` endpoint with DB readiness status and `503` behavior when unhealthy.
- Added `/metrics` endpoint backed by in-memory request counters (status distribution, errors, top endpoints, average latency).
- Request middleware now records observability metrics for both successful and failed requests.
- Updated root README with Docker Compose quickstart and live endpoint URLs for UI/API/health/readiness/metrics.
- Updated production runbook and deploy checklist to include readiness and metrics verification.
