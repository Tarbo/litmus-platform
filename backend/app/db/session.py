from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def build_sessionmaker(database_url: str):
    connect_args = {'check_same_thread': False} if database_url.startswith('sqlite') else {}
    engine = create_engine(database_url, future=True, echo=False, connect_args=connect_args)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False), engine
