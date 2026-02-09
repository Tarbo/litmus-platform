# Milestone 5 Evidence

## Commands run

1. Backend tests (strict warnings)
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/backend
./venv3.12/bin/pytest -q -W error::DeprecationWarning
```

2. Python SDK tests
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
- Experiment report export now supports `json` and `csv` formats via API.
- Python SDK now supports experiment/report/export/decision/guardrail/snapshot operations.
