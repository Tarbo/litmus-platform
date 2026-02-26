# Litmus Self-Serve Quickstart

Use this guide when you want to run Litmus locally and execute a full experiment lifecycle quickly.

## 1. Start the platform

Verify Docker daemon first:

```bash
docker info >/dev/null
```

If this fails with `Cannot connect to the Docker daemon`, start Docker Desktop (or your Docker daemon) before continuing.

```bash
docker compose up --build
```

## 2. Validate core endpoints

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/ready
curl -s http://localhost:8000/metrics
```

Expected:
- `/health` returns `{"status":"ok"}`.
- `/ready` returns `200` once database readiness is true.
- `/metrics` returns request counters.

## 3. Run the self-serve smoke lifecycle

```bash
python3 scripts/smoke_self_serve.py --base-url http://localhost:8000
```

If write auth is enabled:

```bash
python3 scripts/smoke_self_serve.py --base-url http://localhost:8000 --token <admin-token>
```

This smoke sequence covers:
- draft experiment creation
- launch
- assignment + event ingestion
- results retrieval
- pause + stop

## 4. Operate from UI

Open:
- `http://localhost:3000/experiments`
- `http://localhost:3000/experiments/new`

Flow:
1. Create a draft experiment with at least two variants.
2. Open experiment detail.
3. Launch with ramp percentage.
4. Open results dashboard and set interval to `minute`.
5. Pause or stop when done.

## 5. Role-based tutorials

- Data scientist visual onboarding: `docs/runbooks/data-scientist-visual-onboarding.md`
- Product owner: `docs/runbooks/product-experiment-owner-playbook.md`
- Engineer integration: `docs/runbooks/engineer-integration-playbook.md`
- Analyst decisions: `docs/runbooks/analyst-results-playbook.md`
- Variant-only + stop: `docs/runbooks/variant-only-stop-playbook.md`
- Five-model live bandit simulation: `docs/runbooks/live-bandit-5-model-tutorial.md`
