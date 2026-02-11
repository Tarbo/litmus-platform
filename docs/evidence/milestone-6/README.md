# Milestone 6 Evidence

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
- Write endpoints require bearer token when `ADMIN_API_TOKENS` is configured.
- Sensitive POST endpoints are protected by in-memory rate limiting.
- Responses include `X-Request-ID`; errors return structured payloads with request id.
- CI workflow validates backend/sdk/frontend on each PR/push to `litmus_setup`.
