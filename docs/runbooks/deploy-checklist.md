# Deploy Checklist

- [ ] Backend tests pass with strict warnings.
- [ ] SDK tests pass from `sdk` directory.
- [ ] Frontend build succeeds.
- [ ] API contract reviewed (`docs/api/contract.md`).
- [ ] `ADMIN_API_TOKENS` configured in target environment.
- [ ] Rate limit defaults reviewed for expected traffic.
- [ ] Rollback target commit identified.
- [ ] `/health` and `/ready` return healthy status post deploy.
- [ ] `/metrics` is reachable and request counters move during smoke checks.
- [ ] `python3 scripts/smoke_self_serve.py --base-url <url> --token <token>` passes.
- [ ] Post-deploy smoke checks completed and captured.
