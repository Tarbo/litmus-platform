# Milestone 13 Evidence

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

3. Frontend build (Nuxt)
```bash
cd /Users/ezeme.okwudili/Desktop/litmus-platform/frontend
npm run build
```

## Artifacts
- `backend-pytest.txt`
- `sdk-pytest.txt`
- `frontend-build.txt`

## Feature evidence
- Replaced Next.js frontend with Nuxt 3 (Vue) application structure.
- Added Figma-themed visual system and navigation shell tuned for experimentation workflows.
- Implemented experiment list + filters, create form, and detail lifecycle controls (launch/pause/stop/ramp).
- Implemented results dashboard view with exposure totals, metric summaries, and lift table from `/results/{experiment_id}`.
- Implemented settings page for PATCH updates to experiment metadata and targeting.
- Updated docs and Docker frontend runtime path for Nuxt production builds.
