import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.config import settings
from app.core.observability import InMemoryRequestMetrics
from app.core.rate_limit import InMemoryRateLimiter
from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.errors import http_exception_handler, unhandled_exception_handler
from app.middleware import rate_limit_middleware, request_context_middleware
from app.models import Base  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.decision_audit import DecisionAudit  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.experiment import Experiment  # noqa: F401
from app.models.metric import Metric  # noqa: F401
from app.models.report_snapshot import ReportSnapshot  # noqa: F401
from app.models.variant import Variant  # noqa: F401


def create_app(database_url: str | None = None) -> FastAPI:
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        session_maker, engine = build_sessionmaker(database_url or settings.database_url)
        app.state.session_maker = session_maker
        app.state.engine = engine
        app.state.request_metrics = InMemoryRequestMetrics()
        app.state.rate_limiter = InMemoryRateLimiter()
        app.state.rate_limit_per_minute = settings.rate_limit_per_minute
        init_db(engine)
        # Startup preflight: fail fast if database connectivity is unhealthy.
        with engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        yield
        engine.dispose()

    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    origins = [origin.strip() for origin in settings.cors_allowed_origins.split(',') if origin.strip()]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    application.middleware('http')(request_context_middleware)
    application.middleware('http')(rate_limit_middleware)
    application.add_exception_handler(HTTPException, http_exception_handler)
    application.add_exception_handler(Exception, unhandled_exception_handler)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/ready')
def readiness():
    checks = {'database': False}
    try:
        with app.state.engine.connect() as connection:
            connection.execute(text('SELECT 1'))
        checks['database'] = True
    except Exception:
        checks['database'] = False

    payload = {
        'status': 'ready' if all(checks.values()) else 'not_ready',
        'checks': checks,
    }
    if all(checks.values()):
        return payload
    return JSONResponse(status_code=503, content=payload)


@app.get('/metrics')
def metrics():
    return app.state.request_metrics.snapshot()
