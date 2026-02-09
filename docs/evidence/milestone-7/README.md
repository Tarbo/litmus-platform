# Milestone 7 Evidence

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
- Assignment service now uses Thompson Sampling posteriors built from live exposure/conversion events.
- Experiment report payload now includes `assignment_policy` and `bandit_state` diagnostics (posterior alpha/beta, expected conversion rate, win probability).
- Experiment detail UI now renders a realtime "Bandit Live State" table driven by websocket report updates.
- Added milestone-7 backend integration tests validating adaptive traffic shift and report bandit metadata.
