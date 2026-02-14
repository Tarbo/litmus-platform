# End-to-End Live Bandit Tutorial (5 Models)

This tutorial runs a five-model Thompson-sampling experiment and lets you watch decisions, rewards, and event flow while traffic converges. You then manually kill the experiment.

## What this tutorial demonstrates
- Assignment decisions changing over time.
- New exposure/reward/conversion events entering continuously.
- Bandit posterior movement (`alpha`, `beta`, `expected_rate`, `win_probability`).
- Convergence detection based on win probability + sample depth.
- Manual kill (`stop`) by operator.

## 1. Start stack

```bash
docker compose up --build
```

## 2. Run simulator

```bash
python3 scripts/live_bandit_simulation.py --base-url http://localhost:8000
```

If write auth is enabled:

```bash
python3 scripts/live_bandit_simulation.py --base-url http://localhost:8000 --token <admin-token>
```

Optional tuning:

```bash
python3 scripts/live_bandit_simulation.py \
  --base-url http://localhost:8000 \
  --iterations 2500 \
  --report-every 25 \
  --convergence-win-prob 0.92 \
  --min-exposures-per-variant 80
```

## 3. Watch live dashboard

After startup, the script prints experiment URLs:
- Detail page: `http://localhost:3000/experiments/<id>`
- Results page: `http://localhost:3000/experiments/<id>/results`

What to watch:
- Detail page exposure totals update near real-time.
- Results page (interval `minute`, auto-refresh `On`) updates lift/metrics.
- Terminal `live_snapshot` lines show top variant and win probability trajectory.

## 4. Observe convergence

The simulator reports:
- `converged` when top variant reaches configured win probability threshold and minimum exposures.
- `manual_kill_required` with exact UI/API stop path.

## 5. Kill experiment manually

From UI:
- Open detail page and click `Stop`.

Or API:

```bash
curl -s -X POST http://localhost:8000/api/v1/experiments/<id>/stop \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <admin-token>' \
  -d '{"actor":"tutorial.user","reason":"convergence reached"}'
```

## 6. Optional websocket live report stream

The backend also exposes websocket live report stream:
- `ws://localhost:8000/api/v1/ws/experiments/<id>/live`

This stream emits report snapshots every 2 seconds for custom live dashboards.
