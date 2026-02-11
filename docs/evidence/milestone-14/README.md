# Milestone 14 Evidence

## Commands run

1. Backend tests
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform
PYENV_VERSION=3.12.2 python -m pytest -q backend/tests
```

2. SDK tests
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform
PYENV_VERSION=3.12.2 python -m pytest -q sdk/python/tests
```

3. Frontend build
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/frontend
npm run build
```

4. Smoke script contract check
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform
python3 scripts/smoke_self_serve.py --help
```

## Artifacts
- `backend-pytest.txt`
- `sdk-pytest.txt`
- `frontend-build.txt`
- `smoke-script-help.txt`

## Feature evidence
- Added production-ready self-serve smoke script (`scripts/smoke_self_serve.py`) for full experiment lifecycle validation.
- Added backend integration smoke coverage (`backend/tests/test_integration_milestone14_smoke.py`).
- Added API contract documentation (`docs/api/contract.md`) for core endpoints and error semantics.
- Updated Docker Compose frontend runtime env to Nuxt API contract (`NUXT_PUBLIC_API_BASE`).
- Updated deployment runbooks/checklists with deterministic smoke procedure and contract references.
