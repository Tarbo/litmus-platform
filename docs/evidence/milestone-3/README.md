# Milestone 3 Evidence

## Commands run

1. Backend tests (strict warnings)
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/backend
./venv3.12/bin/pytest -q -W error::DeprecationWarning
```

2. Frontend build
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/frontend
npm run build
```

## Artifacts
- `backend-pytest.txt`
- `frontend-build.txt`

## Feature evidence
- Backend now persists guardrail metrics and report snapshots.
- Experiment report endpoint can auto-transition running experiments after decision threshold.
- Frontend experiment detail includes guardrail logging and snapshot history.
