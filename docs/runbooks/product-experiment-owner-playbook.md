# Product / Experiment Owner Playbook

Use this playbook to create, launch, monitor, and safely end experiments.

## Goal
- Define hypothesis and winning metric.
- Ship controlled traffic to variants.
- Decide whether to continue, pause, or stop.

## Step-by-step

1. Create draft
- Go to `http://localhost:3000/experiments/new`.
- Add name, description, owner team, tags, targeting, and variants.
- Keep status as draft until review is complete.

2. Launch
- Open experiment detail page.
- Set `ramp %` to safe initial value (for example 10).
- Click `Launch / Update Ramp`.

3. Monitor
- Watch near real-time exposure totals on detail page.
- Open results page (`/experiments/{id}/results`) for lift and metric summaries.

4. Decide
- Continue when signal is weak.
- Pause for temporary safety checks.
- Stop when guardrails breach or a winner is confirmed and rollout will proceed outside the experiment.

5. Kill switch
- Use `Stop` from experiment detail for immediate termination semantics.
- Add a reason in API operations: `POST /api/v1/experiments/{id}/stop`.

## Operating rules
- Never jump from 0 to 100 ramp for unknown variants.
- Require explicit owner/analyst sign-off before stopping as winner.
- Keep decision notes and report exports for audit history.
