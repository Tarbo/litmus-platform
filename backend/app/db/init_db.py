from sqlalchemy.engine import Engine

from app.models import Base


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(bind=engine)
