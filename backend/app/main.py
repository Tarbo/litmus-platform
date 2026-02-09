from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.config import settings
from app.db.init_db import init_db
from app.db.session import build_sessionmaker
from app.models import Base  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.decision_audit import DecisionAudit  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.experiment import Experiment  # noqa: F401
from app.models.metric import Metric  # noqa: F401
from app.models.report_snapshot import ReportSnapshot  # noqa: F401
from app.models.variant import Variant  # noqa: F401


def create_app(database_url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        session_maker, engine = build_sessionmaker(database_url or settings.database_url)
        app.state.session_maker = session_maker
        app.state.engine = engine
        init_db(engine)
        yield
        engine.dispose()

    application = FastAPI(title=settings.app_name, lifespan=lifespan)
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()


@app.get('/health')
def health():
    return {'status': 'ok'}
