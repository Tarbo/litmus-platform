# Milestone 12 Evidence

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

## Artifacts
- `backend-pytest.txt`
- `sdk-pytest.txt`
- `frontend-build.txt`

## Feature evidence
- Added SDK `ExperimentClient` with `get_variant` aligned to `/api/v1/assignments`.
- Added in-memory assignment caching with TTL and deterministic cache keying by assignment inputs.
- Added retry handling for transient backend errors and configurable fail-safe fallback to control variant.
- Added SDK exposure/metric batching with automatic threshold flush and explicit `flush()` support.
- Added focused SDK unit tests for caching, retries, fail-safe behavior, and batching/flush contract.
- Updated README SDK integration example for self-serve DS/Product team usage.
