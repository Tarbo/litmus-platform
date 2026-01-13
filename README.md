# Litmus Platform

A/B Testing & Experimentation Platform — enterprise-grade patterns.

## Overview

Litmus is a full-stack experimentation platform for running A/B tests, A/B/n tests, and multi-armed bandit experiments with real-time analytics and statistical rigor.

## Features

- **Experiment Management** — Create, configure, and manage A/B and multivariate experiments
- **Traffic Allocation** — Flexible traffic splitting with percentage-based controls
- **User Assignment** — Deterministic bucketing with Redis caching
- **Event Tracking** — High-throughput event ingestion with TimescaleDB
- **Real-time Dashboard** — Live metrics via WebSocket + Redis Pub/Sub
- **Statistical Analysis** — T-tests, chi-squared tests, confidence intervals
- **Multi-armed Bandits** — Thompson Sampling, UCB, Epsilon-Greedy algorithms
- **Auto-insights** — Automated anomaly detection and recommendations

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 (App Router), shadcn/ui, Tailwind CSS, Tremor |
| Backend | FastAPI, WebSockets |
| Database | PostgreSQL + TimescaleDB |
| Cache & Pub/Sub | Redis |
| Task Queue | Celery |
| Statistics | scipy, statsmodels |
| Containerization | Docker Compose |

## Project Structure

```
litmus-platform/
├── frontend/           # Next.js 14 application
│   └── src/
│       ├── app/        # App Router pages
│       ├── components/ # React components
│       ├── hooks/      # Custom hooks
│       ├── lib/        # Utilities
│       └── types/      # TypeScript types
│
├── backend/            # FastAPI application
│   └── app/
│       ├── api/        # REST & WebSocket endpoints
│       ├── core/       # Business logic (assignment, statistics, bandits)
│       ├── models/     # SQLAlchemy models
│       ├── schemas/    # Pydantic schemas
│       ├── services/   # Service layer
│       ├── workers/    # Celery tasks
│       └── db/         # Database utilities
│
├── sdk/                # Client SDKs
│   └── python/         # Python SDK
│
└── scripts/            # Utility scripts
```

## License

See [LICENSE](./LICENSE) for details.
