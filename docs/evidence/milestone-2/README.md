# Milestone 2 Evidence

## Commands run

1. Backend tests
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/backend
./venv3.12/bin/pytest -q
```

2. Frontend build check
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/frontend
npm run build
```

3. Sample report generation (includes p-value, CI, recommendation, and diff-in-diff fields)
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/backend
./venv3.12/bin/python - <<'PY'
# script used to generate sample-report.json
PY
```

## Artifacts
- `backend-pytest.txt`: backend unit and integration test output.
- `frontend-build.txt`: frontend build output for this workspace.
- `sample-report.json`: generated example of the full progress report payload.

## Notes
- `frontend-build.txt` currently shows `next: command not found` in this machine state because frontend dependencies are not installed in the working tree.
