# Litmus Production Runbook

## 1. Pre-deploy checklist
- Confirm CI is green (backend strict tests, sdk tests, frontend build).
- Ensure `ADMIN_API_TOKENS` is configured with at least 2 rotated tokens.
- Verify `RATE_LIMIT_PER_MINUTE` for production traffic profile.
- Confirm database backup freshness.
- Review API contract: `docs/api/contract.md`.

## 2. Required environment variables
- `ENVIRONMENT=production`
- `DATABASE_URL=...`
- `ADMIN_API_TOKENS=token1,token2`
- `RATE_LIMIT_PER_MINUTE=120` (adjust by load profile)

## 3. Incident triage
1. Identify failing endpoint and capture `X-Request-ID` from response.
2. Search logs for matching request id.
3. Check `/metrics` for status-code spikes and top endpoint pressure.
4. If 429 spikes appear, evaluate traffic pattern and temporary limit increase.
5. If 401 spikes appear, verify token rotation/distribution.
6. If report decisions look wrong, inspect decision history endpoint and snapshots.

## 4. Rollback
1. Revert to previous release commit.
2. Restart backend workers and API.
3. Validate `/health`, `/ready`, and key read endpoints.
4. Run smoke checks:
   - `python3 scripts/smoke_self_serve.py --base-url <service-base-url> --token <admin-token>`
   - check `/metrics` increments for expected routes
   - validate frontend deployment health

## 5. Post-incident
- Record root cause and remediation in incident log.
- Add regression test if bug escaped test suite.

## 6. Local end-to-end validation before release
1. Start stack:
   - `docker compose up --build`
2. Confirm dependencies:
   - `curl -s http://localhost:8000/health`
   - `curl -s http://localhost:8000/ready`
3. Run smoke flow:
   - `python3 scripts/smoke_self_serve.py --base-url http://localhost:8000`
4. Verify frontend:
   - open `http://localhost:3000`
   - create or inspect experiments via UI screens
